"""
Model configurations for various LLM providers.
Contains context windows, pricing, and tokenizer information.
"""

from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class ModelProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    MISTRAL = "mistral"
    COHERE = "cohere"
    TOGETHER = "together"
    GROQ = "groq"


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    name: str
    provider: ModelProvider
    context_window: int  # Total context window in tokens
    max_output_tokens: int  # Maximum tokens for output
    cost_per_1k_input: float  # Cost per 1000 input tokens (USD)
    cost_per_1k_output: float  # Cost per 1000 output tokens (USD)
    tokenizer_name: Optional[str] = None  # Tokenizer to use
    supports_function_calling: bool = False
    supports_vision: bool = False
    notes: str = ""

    @property
    def max_input_tokens(self) -> int:
        """Calculate maximum input tokens (context window - max output)."""
        return self.context_window - self.max_output_tokens


# Comprehensive model database
MODEL_DATABASE: Dict[str, ModelConfig] = {
    # OpenAI GPT-4 Models
    "gpt-4": ModelConfig(
        name="gpt-4",
        provider=ModelProvider.OPENAI,
        context_window=8192,
        max_output_tokens=4096,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        tokenizer_name="cl100k_base",
        supports_function_calling=True,
        supports_vision=False,
    ),
    "gpt-4-32k": ModelConfig(
        name="gpt-4-32k",
        provider=ModelProvider.OPENAI,
        context_window=32768,
        max_output_tokens=4096,
        cost_per_1k_input=0.06,
        cost_per_1k_output=0.12,
        tokenizer_name="cl100k_base",
        supports_function_calling=True,
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo",
        provider=ModelProvider.OPENAI,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        tokenizer_name="cl100k_base",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4-turbo-preview": ModelConfig(
        name="gpt-4-turbo-preview",
        provider=ModelProvider.OPENAI,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        tokenizer_name="cl100k_base",
        supports_function_calling=True,
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        provider=ModelProvider.OPENAI,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        tokenizer_name="o200k_base",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        context_window=128000,
        max_output_tokens=16384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        tokenizer_name="o200k_base",
        supports_function_calling=True,
        supports_vision=True,
    ),

    # OpenAI GPT-3.5 Models
    "gpt-3.5-turbo": ModelConfig(
        name="gpt-3.5-turbo",
        provider=ModelProvider.OPENAI,
        context_window=16385,
        max_output_tokens=4096,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        tokenizer_name="cl100k_base",
        supports_function_calling=True,
    ),
    "gpt-3.5-turbo-16k": ModelConfig(
        name="gpt-3.5-turbo-16k",
        provider=ModelProvider.OPENAI,
        context_window=16385,
        max_output_tokens=4096,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        tokenizer_name="cl100k_base",
        supports_function_calling=True,
    ),

    # Anthropic Claude Models
    "claude-3-opus-20240229": ModelConfig(
        name="claude-3-opus-20240229",
        provider=ModelProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=4096,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        tokenizer_name="claude",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "claude-3-sonnet-20240229": ModelConfig(
        name="claude-3-sonnet-20240229",
        provider=ModelProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=4096,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        tokenizer_name="claude",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "claude-3-haiku-20240307": ModelConfig(
        name="claude-3-haiku-20240307",
        provider=ModelProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=4096,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        tokenizer_name="claude",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "claude-3-5-sonnet-20241022": ModelConfig(
        name="claude-3-5-sonnet-20241022",
        provider=ModelProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        tokenizer_name="claude",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "claude-3-5-haiku-20241022": ModelConfig(
        name="claude-3-5-haiku-20241022",
        provider=ModelProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=8192,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.005,
        tokenizer_name="claude",
        supports_function_calling=True,
        supports_vision=False,
    ),
    "claude-opus-4-5-20251101": ModelConfig(
        name="claude-opus-4-5-20251101",
        provider=ModelProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=16384,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        tokenizer_name="claude",
        supports_function_calling=True,
        supports_vision=True,
    ),

    # Google Gemini Models
    "gemini-pro": ModelConfig(
        name="gemini-pro",
        provider=ModelProvider.GOOGLE,
        context_window=32760,
        max_output_tokens=8192,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
        tokenizer_name="gemini",
        supports_function_calling=True,
    ),
    "gemini-1.5-pro": ModelConfig(
        name="gemini-1.5-pro",
        provider=ModelProvider.GOOGLE,
        context_window=2000000,
        max_output_tokens=8192,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        tokenizer_name="gemini",
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gemini-1.5-flash": ModelConfig(
        name="gemini-1.5-flash",
        provider=ModelProvider.GOOGLE,
        context_window=1000000,
        max_output_tokens=8192,
        cost_per_1k_input=0.000075,
        cost_per_1k_output=0.0003,
        tokenizer_name="gemini",
        supports_function_calling=True,
        supports_vision=True,
    ),

    # Meta Llama Models
    "llama-2-7b": ModelConfig(
        name="llama-2-7b",
        provider=ModelProvider.META,
        context_window=4096,
        max_output_tokens=2048,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002,
        tokenizer_name="llama",
    ),
    "llama-2-13b": ModelConfig(
        name="llama-2-13b",
        provider=ModelProvider.META,
        context_window=4096,
        max_output_tokens=2048,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00025,
        tokenizer_name="llama",
    ),
    "llama-2-70b": ModelConfig(
        name="llama-2-70b",
        provider=ModelProvider.META,
        context_window=4096,
        max_output_tokens=2048,
        cost_per_1k_input=0.0009,
        cost_per_1k_output=0.0009,
        tokenizer_name="llama",
    ),
    "llama-3-8b": ModelConfig(
        name="llama-3-8b",
        provider=ModelProvider.META,
        context_window=8192,
        max_output_tokens=4096,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002,
        tokenizer_name="llama",
    ),
    "llama-3-70b": ModelConfig(
        name="llama-3-70b",
        provider=ModelProvider.META,
        context_window=8192,
        max_output_tokens=4096,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079,
        tokenizer_name="llama",
    ),
    "llama-3.1-8b": ModelConfig(
        name="llama-3.1-8b",
        provider=ModelProvider.META,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002,
        tokenizer_name="llama",
    ),
    "llama-3.1-70b": ModelConfig(
        name="llama-3.1-70b",
        provider=ModelProvider.META,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079,
        tokenizer_name="llama",
    ),
    "llama-3.1-405b": ModelConfig(
        name="llama-3.1-405b",
        provider=ModelProvider.META,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.00532,
        cost_per_1k_output=0.016,
        tokenizer_name="llama",
    ),

    # Mistral Models
    "mistral-7b": ModelConfig(
        name="mistral-7b",
        provider=ModelProvider.MISTRAL,
        context_window=32000,
        max_output_tokens=8192,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002,
        tokenizer_name="mistral",
    ),
    "mistral-8x7b": ModelConfig(
        name="mistral-8x7b",
        provider=ModelProvider.MISTRAL,
        context_window=32000,
        max_output_tokens=8192,
        cost_per_1k_input=0.0006,
        cost_per_1k_output=0.0006,
        tokenizer_name="mistral",
    ),
    "mistral-small": ModelConfig(
        name="mistral-small",
        provider=ModelProvider.MISTRAL,
        context_window=32000,
        max_output_tokens=8192,
        cost_per_1k_input=0.002,
        cost_per_1k_output=0.006,
        tokenizer_name="mistral",
        supports_function_calling=True,
    ),
    "mistral-medium": ModelConfig(
        name="mistral-medium",
        provider=ModelProvider.MISTRAL,
        context_window=32000,
        max_output_tokens=8192,
        cost_per_1k_input=0.0027,
        cost_per_1k_output=0.0081,
        tokenizer_name="mistral",
        supports_function_calling=True,
    ),
    "mistral-large": ModelConfig(
        name="mistral-large",
        provider=ModelProvider.MISTRAL,
        context_window=128000,
        max_output_tokens=8192,
        cost_per_1k_input=0.004,
        cost_per_1k_output=0.012,
        tokenizer_name="mistral",
        supports_function_calling=True,
    ),

    # Cohere Models
    "command": ModelConfig(
        name="command",
        provider=ModelProvider.COHERE,
        context_window=4096,
        max_output_tokens=2048,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.002,
        tokenizer_name="cohere",
    ),
    "command-light": ModelConfig(
        name="command-light",
        provider=ModelProvider.COHERE,
        context_window=4096,
        max_output_tokens=2048,
        cost_per_1k_input=0.0003,
        cost_per_1k_output=0.0006,
        tokenizer_name="cohere",
    ),
    "command-r": ModelConfig(
        name="command-r",
        provider=ModelProvider.COHERE,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        tokenizer_name="cohere",
        supports_function_calling=True,
    ),
    "command-r-plus": ModelConfig(
        name="command-r-plus",
        provider=ModelProvider.COHERE,
        context_window=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        tokenizer_name="cohere",
        supports_function_calling=True,
    ),
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    Get model configuration by name.

    Args:
        model_name: Name of the model

    Returns:
        ModelConfig object

    Raises:
        ValueError: If model is not found in database
    """
    if model_name not in MODEL_DATABASE:
        raise ValueError(
            f"Model '{model_name}' not found in database. "
            f"Available models: {', '.join(MODEL_DATABASE.keys())}"
        )
    return MODEL_DATABASE[model_name]


def list_models(provider: Optional[ModelProvider] = None) -> list[str]:
    """
    List all available models, optionally filtered by provider.

    Args:
        provider: Optional provider to filter by

    Returns:
        List of model names
    """
    if provider is None:
        return list(MODEL_DATABASE.keys())
    return [
        name for name, config in MODEL_DATABASE.items()
        if config.provider == provider
    ]


def search_models(
    min_context: Optional[int] = None,
    max_cost_per_1k_input: Optional[float] = None,
    provider: Optional[ModelProvider] = None,
    supports_function_calling: Optional[bool] = None,
    supports_vision: Optional[bool] = None,
) -> list[str]:
    """
    Search for models matching specific criteria.

    Args:
        min_context: Minimum context window size
        max_cost_per_1k_input: Maximum cost per 1k input tokens
        provider: Specific provider
        supports_function_calling: Whether model must support function calling
        supports_vision: Whether model must support vision

    Returns:
        List of matching model names
    """
    results = []

    for name, config in MODEL_DATABASE.items():
        if min_context and config.context_window < min_context:
            continue
        if max_cost_per_1k_input and config.cost_per_1k_input > max_cost_per_1k_input:
            continue
        if provider and config.provider != provider:
            continue
        if supports_function_calling is not None and config.supports_function_calling != supports_function_calling:
            continue
        if supports_vision is not None and config.supports_vision != supports_vision:
            continue

        results.append(name)

    return results
