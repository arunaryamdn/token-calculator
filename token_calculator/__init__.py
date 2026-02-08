"""
Know Your Tokens - LLM Token Optimization and Cost Management

A comprehensive Python package for understanding, analyzing, and optimizing
LLM token usage across different models and providers.
"""

__version__ = "2.2.0"
__author__ = "Know Your Tokens Contributors"

# Alerting
from .alerts import (
    Alert,
    AlertManager,
    AlertRule,
)

# Context analysis
from .context_analyzer import (
    ContextAnalyzer,
    ContextBreakdown,
    ContextStatus,
)

# Conversation management
from .conversation_manager import (
    ConversationManager,
    ConversationStats,
    ConversationTurn,
    Message,
    MessageRole,
)

# Cost calculation
from .cost_calculator import (
    CostBreakdown,
    CostCalculator,
    calculate_cost,
    compare_model_costs,
)

# Cost tracking with labels
from .cost_tracker import (
    Anomaly,
    CostRecord,
    CostReport,
    CostTracker,
    Recommendation,
)

# Cost forecasting and budgeting
from .forecasting import (
    BudgetStatus,
    BudgetTracker,
    CostForecaster,
    Forecast,
    Scenario,
    ScenarioResult,
)

# Context health monitoring
from .health_monitor import (
    CompressionResult,
    ConversationMonitor,
    HealthStatus,
)

# Logging configuration
from .logging_config import (
    configure_logging,
    disable_logging,
    enable_logging,
    get_logger,
)

# Model selection
from .model_selector import (
    ABTestConfig,
    ABTestResults,
    ModelRecommendation,
    ModelSelector,
)

# Core models and configurations
from .models import (
    MODEL_DATABASE,
    ModelConfig,
    ModelProvider,
    get_model_config,
    list_models,
    search_models,
)

# Token optimization
from .optimizer import (
    OptimizationResult,
    OptimizationSuggestion,
    TokenOptimizer,
    optimize_prompt,
    suggest_optimizations,
)

# Storage backends
from .storage import (
    InMemoryStorage,
    SQLiteStorage,
    StorageBackend,
    TrackingEvent,
    create_storage,
)

# Token counting
from .tokenizer import (
    TokenCounter,
    count_messages,
    count_tokens,
)

# Validation and security
from .validation import (
    SecurityError,
    StorageError,
    TokenCalculatorError,
    ValidationError,
    validate_filter_keys,
    validate_group_by,
    validate_message_structure,
    validate_model_name,
    validate_sql_identifier,
    validate_text_size,
    validate_token_counts,
    validate_webhook_url,
)

# Multi-agent workflow tracking
from .workflow_tracker import (
    AgentExecution,
)
from .workflow_tracker import OptimizationSuggestion as WorkflowOptimization
from .workflow_tracker import (
    WorkflowAnalysis,
    WorkflowTracker,
)

# Convenience exports
__all__ = [
    # Version
    "__version__",
    # Models
    "ModelConfig",
    "ModelProvider",
    "MODEL_DATABASE",
    "get_model_config",
    "list_models",
    "search_models",
    # Tokenizer
    "TokenCounter",
    "count_tokens",
    "count_messages",
    # Context
    "ContextAnalyzer",
    "ContextBreakdown",
    "ContextStatus",
    # Cost
    "CostCalculator",
    "CostBreakdown",
    "calculate_cost",
    "compare_model_costs",
    # Conversation
    "ConversationManager",
    "ConversationTurn",
    "ConversationStats",
    "MessageRole",
    "Message",
    # Optimizer
    "TokenOptimizer",
    "OptimizationSuggestion",
    "OptimizationResult",
    "optimize_prompt",
    "suggest_optimizations",
    # Storage
    "StorageBackend",
    "InMemoryStorage",
    "SQLiteStorage",
    "TrackingEvent",
    "create_storage",
    # Cost Tracking
    "CostTracker",
    "CostRecord",
    "CostReport",
    "Anomaly",
    "Recommendation",
    # Workflow Tracking
    "WorkflowTracker",
    "AgentExecution",
    "WorkflowAnalysis",
    "WorkflowOptimization",
    # Health Monitoring
    "ConversationMonitor",
    "HealthStatus",
    "CompressionResult",
    # Forecasting
    "CostForecaster",
    "BudgetTracker",
    "Forecast",
    "Scenario",
    "ScenarioResult",
    "BudgetStatus",
    # Alerts
    "AlertManager",
    "Alert",
    "AlertRule",
    # Model Selection
    "ModelSelector",
    "ModelRecommendation",
    "ABTestConfig",
    "ABTestResults",
    # Validation and Security
    "TokenCalculatorError",
    "ValidationError",
    "SecurityError",
    "StorageError",
    "validate_sql_identifier",
    "validate_webhook_url",
    "validate_filter_keys",
    "validate_group_by",
    "validate_message_structure",
    "validate_text_size",
    "validate_model_name",
    "validate_token_counts",
    # Logging
    "get_logger",
    "configure_logging",
    "disable_logging",
    "enable_logging",
    # Utilities
    "analyze_prompt",
]


# Utility function for quick analysis
def analyze_prompt(
    prompt: str,
    model_name: str = "gpt-4",
    expected_output_tokens: int = 500,
):
    """
    Quick analysis of a prompt with all key metrics.

    Args:
        prompt: The prompt to analyze
        model_name: Model to analyze for (default: gpt-4)
        expected_output_tokens: Expected output length (default: 500)

    Returns:
        Dictionary with comprehensive analysis including:
        - Token count
        - Context usage
        - Cost estimate
        - Optimization suggestions
    """
    # Count tokens
    counter = TokenCounter(model_name)
    tokens = counter.count_tokens(prompt)

    # Analyze context
    analyzer = ContextAnalyzer(model_name)
    messages = [{"role": "user", "content": prompt}]
    context = analyzer.analyze_messages(messages, expected_output_tokens=expected_output_tokens)

    # Calculate cost
    cost_calc = CostCalculator(model_name)
    cost = cost_calc.calculate_cost(tokens, expected_output_tokens)

    # Get optimization suggestions
    optimizer = TokenOptimizer(model_name)
    suggestions = optimizer.suggest_prompt_improvements(prompt)

    return {
        "tokens": {
            "input": tokens,
            "expected_output": expected_output_tokens,
            "total": tokens + expected_output_tokens,
        },
        "context": {
            "usage_percentage": context.usage_percentage,
            "status": context.status.value,
            "available_for_output": context.available_for_output,
            "warnings": context.warnings,
        },
        "cost": {
            "input_cost": cost.input_cost,
            "output_cost": cost.output_cost,
            "total_cost": cost.total_cost,
            "formatted": f"${cost.total_cost:.4f}",
        },
        "optimization": {
            "suggestions_count": len(suggestions),
            "total_potential_savings": sum(s.estimated_tokens_saved for s in suggestions),
            "suggestions": [
                {
                    "strategy": s.strategy,
                    "description": s.description,
                    "tokens_saved": s.estimated_tokens_saved,
                    "impact": s.impact,
                }
                for s in suggestions[:5]  # Top 5 suggestions
            ],
        },
        "model": model_name,
    }
