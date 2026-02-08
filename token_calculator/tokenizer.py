"""
Token counting utilities for various LLM models.
"""

import re
from typing import Any, Dict, List, Optional, Union

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from .models import ModelProvider, get_model_config


class TokenCounter:
    """
    Token counter for various LLM models.
    """

    def __init__(self, model_name: str):
        """
        Initialize token counter for a specific model.

        Args:
            model_name: Name of the model to count tokens for
        """
        self.model_name = model_name
        self.model_config = get_model_config(model_name)
        self._tokenizer = None

    def _get_tokenizer(self):
        """Get or initialize the appropriate tokenizer."""
        if self._tokenizer is not None:
            return self._tokenizer

        tokenizer_name = self.model_config.tokenizer_name

        # OpenAI models use tiktoken
        if tokenizer_name in ["cl100k_base", "o200k_base"]:
            if not TIKTOKEN_AVAILABLE:
                raise ImportError(
                    "tiktoken is required for OpenAI models. "
                    "Install it with: pip install tiktoken"
                )
            self._tokenizer = tiktoken.get_encoding(tokenizer_name)
            return self._tokenizer

        # For other models, use approximate counting
        # This is a fallback - users should install model-specific tokenizers
        return None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        tokenizer = self._get_tokenizer()

        if tokenizer is not None:
            # Use actual tokenizer
            return len(tokenizer.encode(text))
        else:
            # Fallback: approximate token counting
            # This is a rough estimate based on common patterns
            return self._approximate_token_count(text)

    def _approximate_token_count(self, text: str) -> int:
        """
        Approximate token count when tokenizer is not available.

        This is based on common heuristics:
        - English: ~4 characters per token
        - Code: ~3 characters per token
        - With whitespace consideration
        """
        # Split on whitespace and punctuation
        words = re.findall(r"\w+|[^\w\s]", text)

        # Approximate: most words are 1-2 tokens
        token_count = 0
        for word in words:
            if len(word) <= 4:
                token_count += 1
            else:
                # Longer words may be multiple tokens
                token_count += (len(word) + 3) // 4

        return token_count

    def count_messages(
        self, messages: List[Dict[str, Any]], include_function_tokens: bool = True
    ) -> Dict[str, int]:
        """
        Count tokens in a list of chat messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            include_function_tokens: Whether to include function/tool call tokens

        Returns:
            Dictionary with token breakdown:
            - total: Total tokens
            - messages: Tokens in message content
            - system: Tokens in system messages
            - user: Tokens in user messages
            - assistant: Tokens in assistant messages
            - functions: Tokens in function definitions/calls
            - overhead: Tokens used for message formatting
        """
        breakdown = {
            "total": 0,
            "messages": 0,
            "system": 0,
            "user": 0,
            "assistant": 0,
            "functions": 0,
            "overhead": 0,
        }

        # Message formatting overhead (varies by model)
        # OpenAI models: ~3-4 tokens per message
        # Anthropic models: minimal overhead
        overhead_per_message = 4 if self.model_config.provider == ModelProvider.OPENAI else 2

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            # Count content tokens
            if content:
                if isinstance(content, str):
                    token_count = self.count_tokens(content)
                elif isinstance(content, list):
                    # Handle multimodal content (text + images)
                    token_count = 0
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                token_count += self.count_tokens(item.get("text", ""))
                            elif item.get("type") == "image_url":
                                # Images typically cost a fixed number of tokens
                                # This varies by model and image size
                                token_count += 765  # Approximate for GPT-4V
                        else:
                            token_count += self.count_tokens(str(item))
                else:
                    token_count = self.count_tokens(str(content))

                breakdown["messages"] += token_count

                # Add to role-specific count
                if role in breakdown:
                    breakdown[role] += token_count

            # Count function/tool tokens
            if include_function_tokens:
                if "function_call" in message:
                    func_tokens = self.count_tokens(str(message["function_call"]))
                    breakdown["functions"] += func_tokens
                    breakdown["messages"] += func_tokens

                if "tool_calls" in message:
                    tool_tokens = self.count_tokens(str(message["tool_calls"]))
                    breakdown["functions"] += tool_tokens
                    breakdown["messages"] += tool_tokens

            # Add overhead
            breakdown["overhead"] += overhead_per_message

        breakdown["total"] = breakdown["messages"] + breakdown["overhead"]
        return breakdown

    def count_function_definitions(self, functions: List[Dict[str, Any]]) -> int:
        """
        Count tokens in function definitions.

        Args:
            functions: List of function definition dictionaries

        Returns:
            Number of tokens
        """
        if not functions:
            return 0

        # Convert to string representation and count
        func_str = str(functions)
        return self.count_tokens(func_str)


def count_tokens(text: str, model_name: str) -> int:
    """
    Convenience function to count tokens in text.

    Args:
        text: Input text (max 10MB)
        model_name: Name of the model

    Returns:
        Number of tokens

    Raises:
        TypeError: If text or model_name are not strings
        ValidationError: If text exceeds maximum size (10MB)
        ValueError: If model_name is not found in MODEL_DATABASE

    Security:
        - Validates text size to prevent DoS attacks
        - Validates model name exists before processing
    """
    from .constants import MAX_TEXT_LENGTH
    from .models import get_model_config
    from .validation import validate_model_name, validate_text_size

    # Type validation
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    if not isinstance(model_name, str):
        raise TypeError(f"model_name must be str, got {type(model_name).__name__}")

    # Size validation (DoS prevention)
    validate_text_size(text, max_length=MAX_TEXT_LENGTH)

    # Model validation (will raise ValueError if not found)
    get_model_config(model_name)

    counter = TokenCounter(model_name)
    return counter.count_tokens(text)


def count_messages(
    messages: List[Dict[str, Any]], model_name: str, include_function_tokens: bool = True
) -> Dict[str, int]:
    """
    Convenience function to count tokens in messages.

    Args:
        messages: List of message dictionaries (each must have 'role' and 'content')
        model_name: Name of the model
        include_function_tokens: Whether to include function tokens

    Returns:
        Dictionary with token breakdown

    Raises:
        TypeError: If messages is not a list or model_name is not a string
        ValidationError: If message structure is invalid
        ValueError: If model_name is not found in MODEL_DATABASE

    Security:
        - Validates message structure to prevent errors
        - Validates model name exists before processing
    """
    from .models import get_model_config
    from .validation import validate_message_structure, validate_model_name

    # Type validation
    if not isinstance(messages, list):
        raise TypeError(f"messages must be list, got {type(messages).__name__}")
    if not isinstance(model_name, str):
        raise TypeError(f"model_name must be str, got {type(model_name).__name__}")

    # Structure validation
    validate_message_structure(messages)

    # Model validation (will raise ValueError if not found)
    get_model_config(model_name)

    counter = TokenCounter(model_name)
    return counter.count_messages(messages, include_function_tokens)
