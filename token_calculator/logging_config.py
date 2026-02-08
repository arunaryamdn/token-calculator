"""
Logging configuration for token-calculator package.

Provides structured logging setup with consistent formatting across all modules.
Replaces print() statements with proper logging for production use.

Usage:
    from token_calculator.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Operation completed", extra={"operation": "save_event"})
    logger.error("Operation failed", extra={"error": str(e)}, exc_info=True)
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get configured logger instance for a module.

    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Optional log level override ("DEBUG", "INFO", "WARNING", "ERROR")

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing event", extra={"event_id": "123"})
        >>> logger.error("Failed to save", extra={"error": "Connection lost"}, exc_info=True)

    Notes:
        - Loggers are hierarchical: token_calculator.storage inherits from token_calculator
        - Use extra={} dict for structured logging with additional context
        - Use exc_info=True to include exception traceback
    """
    # Create logger with full module path
    logger = logging.getLogger(
        f"token_calculator.{name}" if not name.startswith("token_calculator") else name
    )

    # Set level if specified
    if level:
        logger.setLevel(getattr(logging, level.upper()))

    # Add handler only if none exists (prevents duplicate logs)
    if not logger.handlers and not logging.getLogger("token_calculator").handlers:
        handler = logging.StreamHandler()

        # Format: timestamp - logger_name - level - message
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    include_extra: bool = True,
) -> None:
    """Configure package-wide logging settings.

    Args:
        level: Log level for all token_calculator loggers
               ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        format_string: Custom format string (uses default if None)
        include_extra: Whether to include extra fields in log output

    Example:
        >>> from token_calculator.logging_config import configure_logging
        >>> configure_logging(level="DEBUG")  # Enable debug logs
        >>> configure_logging(level="WARNING")  # Only warnings and errors

    Notes:
        - Call this once at the start of your application
        - Affects all loggers under token_calculator namespace
        - Can be called multiple times to change settings
    """
    # Get root logger for token_calculator package
    logger = logging.getLogger("token_calculator")
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create new handler
    handler = logging.StreamHandler()

    # Set format
    if format_string is None:
        if include_extra:
            # Format with support for extra fields
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            # Simple format
            format_string = "%(levelname)s - %(name)s - %(message)s"

    formatter = logging.Formatter(
        fmt=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger (avoid duplicate logs)
    logger.propagate = False


def disable_logging() -> None:
    """Disable all logging for token_calculator package.

    Useful for:
    - Testing environments
    - Library usage where logs are not desired
    - Performance-critical paths

    Example:
        >>> from token_calculator.logging_config import disable_logging
        >>> disable_logging()  # Suppress all logs
    """
    logger = logging.getLogger("token_calculator")
    logger.disabled = True


def enable_logging(level: str = "INFO") -> None:
    """Re-enable logging after calling disable_logging().

    Args:
        level: Log level to set ("DEBUG", "INFO", "WARNING", "ERROR")

    Example:
        >>> from token_calculator.logging_config import enable_logging
        >>> enable_logging(level="DEBUG")
    """
    logger = logging.getLogger("token_calculator")
    logger.disabled = False
    logger.setLevel(getattr(logging, level.upper()))


# ============================================================================
# Helper Functions for Common Log Patterns
# ============================================================================


def log_operation_start(
    logger: logging.Logger,
    operation: str,
    **kwargs,
) -> None:
    """Log the start of an operation with context.

    Args:
        logger: Logger instance
        operation: Operation name (e.g., "save_event", "query_events")
        **kwargs: Additional context fields

    Example:
        >>> logger = get_logger(__name__)
        >>> log_operation_start(logger, "save_event", event_id="abc123")
    """
    logger.debug(
        f"Starting operation: {operation}",
        extra={"operation": operation, **kwargs},
    )


def log_operation_complete(
    logger: logging.Logger,
    operation: str,
    duration_ms: Optional[float] = None,
    **kwargs,
) -> None:
    """Log successful completion of an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Optional operation duration in milliseconds
        **kwargs: Additional context fields

    Example:
        >>> logger = get_logger(__name__)
        >>> log_operation_complete(logger, "save_event", duration_ms=12.5, event_id="abc123")
    """
    extra = {"operation": operation, **kwargs}
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    logger.info(
        f"Operation completed: {operation}",
        extra=extra,
    )


def log_operation_error(
    logger: logging.Logger,
    operation: str,
    error: Exception,
    **kwargs,
) -> None:
    """Log operation failure with error details.

    Args:
        logger: Logger instance
        operation: Operation name
        error: Exception that occurred
        **kwargs: Additional context fields

    Example:
        >>> logger = get_logger(__name__)
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_operation_error(logger, "save_event", e, event_id="abc123")
    """
    logger.error(
        f"Operation failed: {operation}",
        extra={
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs,
        },
        exc_info=True,
    )


# ============================================================================
# Default Configuration
# ============================================================================

# Set default configuration on module import
# Users can call configure_logging() to override
_default_logger = logging.getLogger("token_calculator")
if not _default_logger.handlers:
    # Only configure if not already configured
    # This allows users to set up their own logging before importing
    _default_handler = logging.StreamHandler()
    _default_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _default_handler.setFormatter(_default_formatter)
    _default_logger.addHandler(_default_handler)
    _default_logger.setLevel(logging.INFO)
    _default_logger.propagate = False
