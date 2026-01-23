"""
Know Your Tokens - LLM Token Optimization and Cost Management

A comprehensive Python package for understanding, analyzing, and optimizing
LLM token usage across different models and providers.
"""

__version__ = "0.1.0"
__author__ = "Know Your Tokens Contributors"

# Core models and configurations
from .models import (
    ModelConfig,
    ModelProvider,
    MODEL_DATABASE,
    get_model_config,
    list_models,
    search_models,
)

# Token counting
from .tokenizer import (
    TokenCounter,
    count_tokens,
    count_messages,
)

# Context analysis
from .context_analyzer import (
    ContextAnalyzer,
    ContextBreakdown,
    ContextStatus,
)

# Cost calculation
from .cost_calculator import (
    CostCalculator,
    CostBreakdown,
    calculate_cost,
    compare_model_costs,
)

# Conversation management
from .conversation_manager import (
    ConversationManager,
    ConversationTurn,
    ConversationStats,
    MessageRole,
)

# Token optimization
from .optimizer import (
    TokenOptimizer,
    OptimizationSuggestion,
    OptimizationResult,
    optimize_prompt,
    suggest_optimizations,
)

# Storage backends
from .storage import (
    StorageBackend,
    InMemoryStorage,
    SQLiteStorage,
    TrackingEvent,
    create_storage,
)

# Cost tracking with labels
from .cost_tracker import (
    CostTracker,
    CostRecord,
    CostReport,
    Anomaly,
    Recommendation,
)

# Multi-agent workflow tracking
from .workflow_tracker import (
    WorkflowTracker,
    AgentExecution,
    WorkflowAnalysis,
    OptimizationSuggestion as WorkflowOptimization,
)

# Context health monitoring
from .health_monitor import (
    ConversationMonitor,
    HealthStatus,
    CompressionResult,
)

# Cost forecasting and budgeting
from .forecasting import (
    CostForecaster,
    BudgetTracker,
    Forecast,
    Scenario,
    ScenarioResult,
    BudgetStatus,
)

# Alerting
from .alerts import (
    AlertManager,
    Alert,
    AlertRule,
)

# Model selection
from .model_selector import (
    ModelSelector,
    ModelRecommendation,
    ABTestConfig,
    ABTestResults,
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
