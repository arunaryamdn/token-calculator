"""
Input validation and security checks for token-calculator.

This module provides validation functions to prevent security vulnerabilities:
- SQL injection via filter keys and group_by dimensions
- SSRF attacks via malicious webhook URLs
- DoS attacks via oversized inputs
- Invalid message structures

All validation functions raise descriptive exceptions on invalid input.
"""

import ipaddress
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# ============================================================================
# Custom Exceptions
# ============================================================================


class TokenCalculatorError(Exception):
    """Base exception for token-calculator package."""

    pass


class ValidationError(TokenCalculatorError):
    """Raised when input validation fails."""

    pass


class SecurityError(TokenCalculatorError):
    """Raised when a security check fails (SQL injection, SSRF, etc.)."""

    pass


class StorageError(TokenCalculatorError):
    """Raised when a storage operation fails."""

    pass


# ============================================================================
# SQL Injection Prevention
# ============================================================================


def validate_sql_identifier(name: str, max_length: int = 256) -> str:
    """Validate SQL identifier (label keys, dimension names, group_by fields).

    Args:
        name: Identifier to validate (e.g., "agent_id", "user-123")
        max_length: Maximum allowed length (default: 256)

    Returns:
        The validated identifier (unchanged if valid)

    Raises:
        ValidationError: If identifier contains invalid characters or is too long

    Security:
        Prevents SQL injection by ensuring identifiers only contain safe characters.
        Used for validating filter keys and group_by dimensions before SQL construction.

    Example:
        >>> validate_sql_identifier("agent_id")  # Valid
        'agent_id'
        >>> validate_sql_identifier("user-123")  # Valid
        'user-123'
        >>> validate_sql_identifier("id'; DROP TABLE--")  # Raises ValidationError
    """
    if not isinstance(name, str):
        raise TypeError(f"Identifier must be str, got {type(name).__name__}")

    if not name:
        raise ValidationError("Identifier cannot be empty")

    # Check length
    if len(name) > max_length:
        raise ValidationError(f"Identifier too long: {len(name)} chars (maximum: {max_length})")

    # Only allow alphanumeric, underscore, and hyphen
    # This prevents SQL injection via special characters like quotes, semicolons, etc.
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValidationError(
            f"Invalid identifier: '{name}'. "
            f"Only alphanumeric characters, underscores, and hyphens allowed."
        )

    return name


def validate_filter_keys(filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Validate all keys in a filter dictionary.

    Args:
        filters: Dictionary of filter conditions (keys are validated)

    Returns:
        The same filters dictionary (if valid)

    Raises:
        ValidationError: If any filter key is invalid

    Example:
        >>> validate_filter_keys({"agent_id": "test", "env": "prod"})  # Valid
        {'agent_id': 'test', 'env': 'prod'}
        >>> validate_filter_keys({"id'; DROP--": "x"})  # Raises ValidationError
    """
    if filters is None:
        return None

    if not isinstance(filters, dict):
        raise TypeError(f"Filters must be dict, got {type(filters).__name__}")

    # Validate each key
    for key in filters.keys():
        validate_sql_identifier(key)

    return filters


def validate_group_by(group_by: Optional[List[str]]) -> Optional[List[str]]:
    """Validate group_by dimension names.

    Args:
        group_by: List of dimension names for grouping

    Returns:
        The same list (if valid)

    Raises:
        ValidationError: If any dimension name is invalid

    Example:
        >>> validate_group_by(["agent_id", "model"])  # Valid
        ['agent_id', 'model']
        >>> validate_group_by(["x'; DROP TABLE--"])  # Raises ValidationError
    """
    if group_by is None:
        return None

    if not isinstance(group_by, list):
        raise TypeError(f"group_by must be list, got {type(group_by).__name__}")

    # Validate each dimension
    for dim in group_by:
        if not isinstance(dim, str):
            raise TypeError(f"Dimension must be str, got {type(dim).__name__}")
        validate_sql_identifier(dim)

    return group_by


# ============================================================================
# SSRF Prevention
# ============================================================================


def _is_internal_ip(hostname: str) -> bool:
    """Check if hostname is an internal/private IP address.

    Args:
        hostname: Hostname or IP address to check

    Returns:
        True if hostname is internal, False otherwise

    Internal IPs include:
    - Private networks: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    - Loopback: 127.0.0.0/8
    - Link-local: 169.254.0.0/16 (includes cloud metadata services)
    - Localhost
    """
    # Check for localhost strings
    if hostname.lower() in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
        return True

    # Check if hostname contains localhost
    if "localhost" in hostname.lower():
        return True

    # Try to parse as IP address
    try:
        ip = ipaddress.ip_address(hostname)
        # Check if IP is private, loopback, or link-local
        # (link-local includes 169.254.0.0/16 which contains cloud metadata services)
        return ip.is_private or ip.is_loopback or ip.is_link_local

    except ValueError:
        # Not an IP address, it's a hostname - allow it
        return False


def validate_webhook_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """Validate webhook URL to prevent SSRF attacks.

    Args:
        url: Webhook URL to validate
        allowed_schemes: List of allowed URL schemes (default: ["https"])

    Returns:
        The validated URL (unchanged if valid)

    Raises:
        SecurityError: If URL scheme is not allowed or points to internal IP

    Security:
        Prevents SSRF (Server-Side Request Forgery) attacks by:
        - Enforcing HTTPS by default
        - Blocking requests to internal IPs (10.x.x.x, 192.168.x.x, 127.0.0.1)
        - Blocking localhost and link-local addresses
        - Blocking cloud metadata services (169.254.169.254)

    Example:
        >>> validate_webhook_url("https://hooks.slack.com/...")  # Valid
        'https://hooks.slack.com/...'
        >>> validate_webhook_url("http://localhost/evil")  # Raises SecurityError
        >>> validate_webhook_url("https://192.168.1.1/hack")  # Raises SecurityError
    """
    if not isinstance(url, str):
        raise TypeError(f"URL must be str, got {type(url).__name__}")

    if not url:
        raise ValidationError("URL cannot be empty")

    # Set default allowed schemes (HTTPS only for security)
    if allowed_schemes is None:
        allowed_schemes = ["https"]

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}")

    # Check scheme
    if not parsed.scheme:
        raise ValidationError("URL must include scheme (e.g., https://)")

    if parsed.scheme not in allowed_schemes:
        raise SecurityError(
            f"URL scheme '{parsed.scheme}' not allowed. "
            f"Allowed schemes: {', '.join(allowed_schemes)}. "
            f"To allow HTTP for development, pass allowed_schemes=['http', 'https']."
        )

    # Check hostname
    if not parsed.hostname:
        raise ValidationError("URL must include hostname")

    # Check for cloud metadata service IPs first (for specific error message)
    # AWS: 169.254.169.254, GCP: 169.254.169.254, Azure: 169.254.169.254, 169.254.170.2
    metadata_ips = ["169.254.169.254", "169.254.170.2", "fd00:ec2::254"]
    if parsed.hostname in metadata_ips:
        raise SecurityError(
            f"Cannot send webhooks to cloud metadata service: {parsed.hostname}. "
            f"This prevents credential theft attacks (SSRF)."
        )

    # Block internal IPs (SSRF prevention)
    if _is_internal_ip(parsed.hostname):
        raise SecurityError(
            f"Cannot send webhooks to internal/private IP addresses: {parsed.hostname}. "
            f"This prevents SSRF (Server-Side Request Forgery) attacks."
        )

    return url


# ============================================================================
# Input Validation
# ============================================================================


def validate_message_structure(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate message structure for token counting.

    Args:
        messages: List of message dictionaries

    Returns:
        The same messages list (if valid)

    Raises:
        ValidationError: If message structure is invalid

    Message Requirements:
    - Must be a list of dictionaries
    - Each message must have "role" and "content" fields
    - Role must be a string
    - Content must be a string (or dict for some models)

    Example:
        >>> messages = [
        ...     {"role": "user", "content": "Hello"},
        ...     {"role": "assistant", "content": "Hi!"}
        ... ]
        >>> validate_message_structure(messages)
        [{'role': 'user', 'content': 'Hello'}, ...]
    """
    if not isinstance(messages, list):
        raise TypeError(f"Messages must be list, got {type(messages).__name__}")

    if not messages:
        raise ValidationError("Messages list cannot be empty")

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise ValidationError(f"Message at index {i} must be dict, got {type(msg).__name__}")

        # Check for required fields
        if "role" not in msg:
            raise ValidationError(f"Message at index {i} missing 'role' field")

        if "content" not in msg:
            # Some messages might have function_call instead of content
            if "function_call" not in msg and "tool_calls" not in msg:
                raise ValidationError(
                    f"Message at index {i} missing 'content', 'function_call', "
                    f"or 'tool_calls' field"
                )

        # Validate role
        if not isinstance(msg["role"], str):
            raise ValidationError(
                f"Message at index {i}: role must be str, got {type(msg['role']).__name__}"
            )

        # Validate content (if present)
        if "content" in msg:
            content = msg["content"]
            # Content can be string, list (for vision), or None
            if content is not None:
                if not isinstance(content, (str, list)):
                    raise ValidationError(
                        f"Message at index {i}: content must be str or list, "
                        f"got {type(content).__name__}"
                    )

    return messages


def validate_text_size(text: str, max_length: int = 10_000_000) -> str:
    """Validate text size to prevent DoS attacks.

    Args:
        text: Text to validate
        max_length: Maximum allowed length in characters (default: 10M)

    Returns:
        The same text (if valid)

    Raises:
        ValidationError: If text exceeds maximum length

    Example:
        >>> validate_text_size("Hello")  # Valid
        'Hello'
        >>> validate_text_size("x" * 20_000_000)  # Raises ValidationError
    """
    if not isinstance(text, str):
        raise TypeError(f"Text must be str, got {type(text).__name__}")

    if len(text) > max_length:
        raise ValidationError(
            f"Text too large: {len(text):,} characters. "
            f"Maximum allowed: {max_length:,} characters. "
            f"Large texts can cause performance issues and timeouts."
        )

    return text


def validate_model_name(model_name: str) -> str:
    """Validate model name format.

    Args:
        model_name: Model name to validate

    Returns:
        The same model name (if valid)

    Raises:
        TypeError: If model_name is not a string
        ValidationError: If model_name is empty

    Example:
        >>> validate_model_name("gpt-4")  # Valid
        'gpt-4'
        >>> validate_model_name("")  # Raises ValidationError
    """
    if not isinstance(model_name, str):
        raise TypeError(f"Model name must be str, got {type(model_name).__name__}")

    if not model_name:
        raise ValidationError("Model name cannot be empty")

    return model_name


def validate_token_counts(
    input_tokens: int, output_tokens: int, max_tokens: int = 1_000_000
) -> None:
    """Validate token counts are reasonable.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        max_tokens: Maximum allowed tokens per field (default: 1M)

    Raises:
        TypeError: If tokens are not integers
        ValidationError: If token counts are negative or exceed maximum

    Example:
        >>> validate_token_counts(1000, 500)  # Valid
        >>> validate_token_counts(-10, 100)  # Raises ValidationError
        >>> validate_token_counts(2_000_000, 500)  # Raises ValidationError
    """
    if not isinstance(input_tokens, int):
        raise TypeError(f"input_tokens must be int, got {type(input_tokens).__name__}")

    if not isinstance(output_tokens, int):
        raise TypeError(f"output_tokens must be int, got {type(output_tokens).__name__}")

    if input_tokens < 0:
        raise ValidationError(f"input_tokens cannot be negative: {input_tokens}")

    if output_tokens < 0:
        raise ValidationError(f"output_tokens cannot be negative: {output_tokens}")

    if input_tokens > max_tokens:
        raise ValidationError(f"input_tokens too large: {input_tokens:,} (maximum: {max_tokens:,})")

    if output_tokens > max_tokens:
        raise ValidationError(
            f"output_tokens too large: {output_tokens:,} (maximum: {max_tokens:,})"
        )
