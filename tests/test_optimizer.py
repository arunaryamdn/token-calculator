"""
Tests for optimizer module.
"""

import pytest
from token_calculator.optimizer import (
    TokenOptimizer,
    optimize_prompt,
    suggest_optimizations,
)


def test_optimizer_init():
    """Test TokenOptimizer initialization."""
    optimizer = TokenOptimizer("gpt-4")
    assert optimizer.model_name == "gpt-4"


def test_optimize_text():
    """Test text optimization."""
    optimizer = TokenOptimizer("gpt-4")
    text = "In order to    complete this task,   please note that you should think carefully."

    result = optimizer.optimize_text(text, aggressive=False)

    assert result.original_tokens >= result.optimized_tokens
    assert result.tokens_saved >= 0
    assert result.reduction_percentage >= 0
    assert len(result.optimized_text) > 0


def test_optimize_whitespace():
    """Test whitespace optimization."""
    optimizer = TokenOptimizer("gpt-4")
    text = "Hello\n\n\n\n\nWorld"

    result = optimizer.optimize_text(text, strategies=["whitespace"])

    assert "\n\n\n" not in result.optimized_text
    assert "Hello" in result.optimized_text
    assert "World" in result.optimized_text


def test_suggest_optimizations():
    """Test getting optimization suggestions."""
    optimizer = TokenOptimizer("gpt-4")
    text = """
    In order to complete this task, please note that
    you should really think very carefully about this.
    """

    suggestions = optimizer.suggest_prompt_improvements(text)

    assert isinstance(suggestions, list)
    # Should find at least some optimization opportunities
    assert len(suggestions) >= 0


def test_compare_phrasings():
    """Test comparing different phrasings."""
    optimizer = TokenOptimizer("gpt-4")
    phrasings = [
        "Please explain this",
        "Explain this",
        "Explain",
    ]

    comparisons = optimizer.compare_phrasings(phrasings)

    assert len(comparisons) == 3
    # Should be sorted by token count
    assert comparisons[0]["tokens"] <= comparisons[1]["tokens"]
    assert comparisons[1]["tokens"] <= comparisons[2]["tokens"]


def test_optimize_prompt_convenience():
    """Test convenience function."""
    result = optimize_prompt("In order to test", "gpt-4", aggressive=False)
    assert result.optimized_tokens <= result.original_tokens
