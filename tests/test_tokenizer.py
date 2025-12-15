"""
Tests for tokenizer module.
"""

import pytest
from token_calculator.tokenizer import TokenCounter, count_tokens, count_messages


def test_token_counter_init():
    """Test TokenCounter initialization."""
    counter = TokenCounter("gpt-4")
    assert counter.model_name == "gpt-4"
    assert counter.model_config is not None


def test_count_tokens_basic():
    """Test basic token counting."""
    counter = TokenCounter("gpt-4")
    tokens = counter.count_tokens("Hello, world!")
    assert tokens > 0
    assert isinstance(tokens, int)


def test_count_tokens_empty():
    """Test counting tokens in empty string."""
    counter = TokenCounter("gpt-4")
    tokens = counter.count_tokens("")
    assert tokens == 0


def test_count_messages():
    """Test counting tokens in messages."""
    counter = TokenCounter("gpt-4")
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    breakdown = counter.count_messages(messages)

    assert breakdown["total"] > 0
    assert breakdown["system"] > 0
    assert breakdown["user"] > 0
    assert breakdown["assistant"] > 0
    assert breakdown["overhead"] > 0


def test_count_tokens_convenience():
    """Test convenience function."""
    tokens = count_tokens("Test message", "gpt-4")
    assert tokens > 0


def test_count_messages_convenience():
    """Test convenience function for messages."""
    messages = [{"role": "user", "content": "Test"}]
    breakdown = count_messages(messages, "gpt-4")
    assert breakdown["total"] > 0
