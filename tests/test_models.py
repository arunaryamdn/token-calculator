"""
Tests for models module.
"""

import pytest
from token_calculator.models import (
    get_model_config,
    list_models,
    search_models,
    ModelProvider,
)


def test_get_model_config():
    """Test getting model configuration."""
    config = get_model_config("gpt-4")
    assert config.name == "gpt-4"
    assert config.provider == ModelProvider.OPENAI
    assert config.context_window > 0
    assert config.max_output_tokens > 0
    assert config.cost_per_1k_input > 0


def test_get_invalid_model():
    """Test getting invalid model raises error."""
    with pytest.raises(ValueError):
        get_model_config("invalid-model-name")


def test_list_models():
    """Test listing models."""
    all_models = list_models()
    assert len(all_models) > 0

    openai_models = list_models(provider=ModelProvider.OPENAI)
    assert len(openai_models) > 0
    assert "gpt-4" in openai_models


def test_search_models():
    """Test searching models."""
    # Search for models with large context
    large_context = search_models(min_context=100000)
    assert len(large_context) > 0

    # Search for cheap models
    cheap_models = search_models(max_cost_per_1k_input=0.001)
    assert len(cheap_models) > 0

    # Search for models with function calling
    function_models = search_models(supports_function_calling=True)
    assert len(function_models) > 0


def test_model_config_properties():
    """Test model config calculated properties."""
    config = get_model_config("gpt-4")
    assert config.max_input_tokens == config.context_window - config.max_output_tokens
