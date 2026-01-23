"""Model recommendation engine for optimal cost/quality trade-offs."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .models import MODEL_DATABASE, ModelConfig, get_model_config
from .storage import StorageBackend


@dataclass
class ModelRecommendation:
    """Model recommendation with cost/quality analysis.

    Attributes:
        suggested_model: Recommended model
        current_model: Current model (if applicable)
        monthly_savings: Estimated monthly savings
        quality_delta: Estimated quality impact (-100 to 100, 0 = no change)
        confidence: Confidence level (0-1)
        reasoning: Explanation of recommendation
        alternative_models: Other models to consider
    """

    suggested_model: str
    current_model: Optional[str]
    monthly_savings: float
    quality_delta: float
    confidence: float
    reasoning: str
    alternative_models: List[str]

    def __str__(self) -> str:
        """String representation."""
        confidence_pct = self.confidence * 100

        lines = [
            f"💡 Model Recommendation: {self.suggested_model}",
        ]

        if self.current_model:
            lines.append(f"   Current: {self.current_model}")

        lines.extend([
            f"   Monthly Savings: ${self.monthly_savings:.2f}",
            f"   Quality Impact: {self.quality_delta:+.0f}%",
            f"   Confidence: {confidence_pct:.0f}%",
            f"   Reasoning: {self.reasoning}",
        ])

        if self.alternative_models:
            lines.append(
                f"   Alternatives: {', '.join(self.alternative_models)}"
            )

        return "\n".join(lines)


@dataclass
class ABTestConfig:
    """A/B test configuration.

    Attributes:
        name: Test name
        model_a: Control model
        model_b: Experiment model
        traffic_split: Traffic split for model_b (0-1, e.g., 0.1 = 10%)
        duration_days: Test duration in days
        start_time: Test start time
        metrics: Metrics to track
    """

    name: str
    model_a: str
    model_b: str
    traffic_split: float
    duration_days: int
    start_time: datetime
    metrics: List[str]


@dataclass
class ABTestResults:
    """A/B test results.

    Attributes:
        test: Original test configuration
        model_a_cost: Average cost for model A
        model_b_cost: Average cost for model B
        cost_delta_pct: Cost difference percentage
        model_a_calls: Number of calls to model A
        model_b_calls: Number of calls to model B
        quality_delta: Quality difference (if measurable)
        recommendation: Recommendation based on results
    """

    test: ABTestConfig
    model_a_cost: float
    model_b_cost: float
    cost_delta_pct: float
    model_a_calls: int
    model_b_calls: int
    quality_delta: Optional[float]
    recommendation: str

    def __str__(self) -> str:
        """String representation."""
        winner = "Model B" if self.cost_delta_pct < -10 else "Model A"

        return (
            f"A/B Test Results: {self.test.name}\n"
            f"  Model A ({self.test.model_a}):\n"
            f"    Calls: {self.model_a_calls}\n"
            f"    Avg Cost: ${self.model_a_cost:.4f}\n"
            f"  Model B ({self.test.model_b}):\n"
            f"    Calls: {self.model_b_calls}\n"
            f"    Avg Cost: ${self.model_b_cost:.4f}\n"
            f"  Cost Delta: {self.cost_delta_pct:+.1f}%\n"
            f"  Winner: {winner}\n"
            f"  Recommendation: {self.recommendation}"
        )


class ModelSelector:
    """Recommend optimal models based on usage patterns.

    Analyzes usage patterns and requirements to recommend the best
    model for cost/quality trade-offs. Supports A/B testing different
    models to validate recommendations.

    Args:
        storage: Optional storage backend for historical analysis

    Example:
        >>> from token_calculator import ModelSelector
        >>> selector = ModelSelector()
        >>> rec = selector.recommend(
        ...     current_model="gpt-4",
        ...     requirements={"max_cost_per_1k": 0.01}
        ... )
        >>> print(rec)
    """

    def __init__(self, storage: Optional[StorageBackend] = None):
        """Initialize model selector.

        Args:
            storage: Optional storage backend
        """
        self.storage = storage
        self.active_tests: Dict[str, ABTestConfig] = {}

    def recommend(
        self,
        current_model: Optional[str] = None,
        requirements: Optional[Dict[str, any]] = None,
        usage_context: Optional[str] = None,
    ) -> ModelRecommendation:
        """Recommend best model for requirements.

        Args:
            current_model: Current model (if any)
            requirements: Requirements dict with keys:
                - max_cost_per_1k: Maximum cost per 1K tokens
                - min_context: Minimum context window
                - min_quality_score: Minimum quality score
            usage_context: Usage context (e.g., "simple_qa", "complex_reasoning", "code_generation")

        Returns:
            ModelRecommendation with suggested model

        Example:
            >>> rec = selector.recommend(
            ...     current_model="gpt-4",
            ...     requirements={"max_cost_per_1k": 0.01},
            ...     usage_context="simple_qa"
            ... )
            >>> if rec.monthly_savings > 100:
            ...     print(f"Switch to {rec.suggested_model}!")
        """
        requirements = requirements or {}

        # Get candidate models
        candidates = self._get_candidate_models(requirements)

        if not candidates:
            return ModelRecommendation(
                suggested_model=current_model or "gpt-4o",
                current_model=current_model,
                monthly_savings=0,
                quality_delta=0,
                confidence=0.5,
                reasoning="No models match requirements",
                alternative_models=[],
            )

        # Score candidates
        scored = []
        for model_name, config in candidates.items():
            score = self._score_model(
                config,
                requirements,
                usage_context,
            )
            scored.append((model_name, config, score))

        # Sort by score (higher is better)
        scored.sort(key=lambda x: x[2], reverse=True)

        # Best model
        best_model, best_config, best_score = scored[0]

        # Calculate savings if we have current model
        monthly_savings = 0
        if current_model and self.storage:
            monthly_savings = self._estimate_savings(
                current_model,
                best_model,
            )

        # Estimate quality delta
        quality_delta = self._estimate_quality_delta(
            current_model,
            best_model,
            usage_context,
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            current_model,
            best_model,
            best_config,
            usage_context,
        )

        # Alternative models
        alternatives = [name for name, _, _ in scored[1:4]]

        # Confidence based on score and data availability
        confidence = 0.7 if self.storage else 0.5

        return ModelRecommendation(
            suggested_model=best_model,
            current_model=current_model,
            monthly_savings=monthly_savings,
            quality_delta=quality_delta,
            confidence=confidence,
            reasoning=reasoning,
            alternative_models=alternatives,
        )

    def create_ab_test(
        self,
        name: str,
        model_a: str,
        model_b: str,
        traffic_split: float = 0.1,
        duration_days: int = 7,
    ) -> ABTestConfig:
        """Create an A/B test comparing two models.

        Args:
            name: Test name
            model_a: Control model
            model_b: Experiment model
            traffic_split: Percentage of traffic to model_b (0-1)
            duration_days: Test duration

        Returns:
            ABTestConfig

        Example:
            >>> test = selector.create_ab_test(
            ...     name="gpt4-vs-gpt4o",
            ...     model_a="gpt-4",
            ...     model_b="gpt-4o",
            ...     traffic_split=0.1,
            ...     duration_days=7
            ... )
            >>> # After 7 days...
            >>> results = selector.get_test_results(test)
            >>> print(results)
        """
        test = ABTestConfig(
            name=name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split,
            duration_days=duration_days,
            start_time=datetime.now(),
            metrics=["cost", "latency", "quality"],
        )

        self.active_tests[name] = test
        return test

    def get_test_results(self, test: ABTestConfig) -> ABTestResults:
        """Get A/B test results.

        Args:
            test: Test configuration

        Returns:
            ABTestResults with analysis

        Example:
            >>> results = selector.get_test_results(test)
            >>> if results.cost_delta_pct < -20:
            ...     print("Model B saves >20%!")
        """
        if not self.storage:
            raise ValueError("Storage backend required for A/B test results")

        # Query costs for both models
        end_time = test.start_time + timedelta(days=test.duration_days)

        # Model A costs
        model_a_data = self.storage.query_events(
            filters={"model": test.model_a},
            start_time=test.start_time,
            end_time=end_time,
        )

        # Model B costs
        model_b_data = self.storage.query_events(
            filters={"model": test.model_b},
            start_time=test.start_time,
            end_time=end_time,
        )

        # Calculate averages
        model_a_calls = len(model_a_data)
        model_b_calls = len(model_b_data)

        model_a_cost = (
            sum(e.cost for e in model_a_data) / model_a_calls
            if model_a_calls > 0
            else 0
        )

        model_b_cost = (
            sum(e.cost for e in model_b_data) / model_b_calls
            if model_b_calls > 0
            else 0
        )

        # Calculate delta
        cost_delta_pct = (
            ((model_b_cost - model_a_cost) / model_a_cost * 100)
            if model_a_cost > 0
            else 0
        )

        # Generate recommendation
        if cost_delta_pct < -20:
            recommendation = f"Switch to {test.model_b} for >20% cost savings"
        elif cost_delta_pct < -10:
            recommendation = f"Consider switching to {test.model_b} for cost savings"
        elif cost_delta_pct > 20:
            recommendation = f"Keep {test.model_a} - {test.model_b} is more expensive"
        else:
            recommendation = "Costs similar - choose based on other factors"

        return ABTestResults(
            test=test,
            model_a_cost=model_a_cost,
            model_b_cost=model_b_cost,
            cost_delta_pct=cost_delta_pct,
            model_a_calls=model_a_calls,
            model_b_calls=model_b_calls,
            quality_delta=None,  # Would need quality metrics
            recommendation=recommendation,
        )

    def _get_candidate_models(
        self,
        requirements: Dict[str, any],
    ) -> Dict[str, ModelConfig]:
        """Get models matching requirements."""
        candidates = {}

        for name, config in MODEL_DATABASE.items():
            # Check cost requirement
            max_cost = requirements.get("max_cost_per_1k")
            if max_cost and config.cost_per_1k_input > max_cost:
                continue

            # Check context requirement
            min_context = requirements.get("min_context")
            if min_context and config.max_input_tokens < min_context:
                continue

            candidates[name] = config

        return candidates

    def _score_model(
        self,
        config: ModelConfig,
        requirements: Dict[str, any],
        usage_context: Optional[str],
    ) -> float:
        """Score a model (higher is better)."""
        score = 0.0

        # Prefer lower cost (normalize to 0-100)
        # Assuming max cost is $0.10 per 1K tokens
        cost_score = max(0, 100 - (config.cost_per_1k_input / 0.10 * 100))
        score += cost_score * 0.5  # 50% weight on cost

        # Prefer larger context
        # Normalize to 0-100 (assuming max 2M tokens)
        context_score = min(100, config.max_input_tokens / 20000)
        score += context_score * 0.3  # 30% weight on context

        # Usage context bonus
        if usage_context == "simple_qa":
            # Prefer fast, cheap models
            if "mini" in config.model_name or "haiku" in config.model_name:
                score += 20
        elif usage_context == "complex_reasoning":
            # Prefer powerful models
            if "gpt-4" in config.model_name or "opus" in config.model_name:
                score += 20
        elif usage_context == "code_generation":
            # Prefer code-optimized models
            if "gpt-4" in config.model_name:
                score += 10

        return score

    def _estimate_savings(
        self,
        current_model: str,
        suggested_model: str,
    ) -> float:
        """Estimate monthly savings from switching models."""
        if not self.storage:
            return 0

        # Get recent usage
        now = datetime.now()
        start_time = now - timedelta(days=30)

        events = self.storage.query_events(
            filters={"model": current_model},
            start_time=start_time,
            end_time=now,
        )

        if not events:
            return 0

        # Current monthly cost
        current_cost = sum(e.cost for e in events)

        # Estimate new cost
        current_config = get_model_config(current_model)
        new_config = get_model_config(suggested_model)

        cost_ratio = new_config.cost_per_1k_input / current_config.cost_per_1k_input
        estimated_new_cost = current_cost * cost_ratio

        return current_cost - estimated_new_cost

    def _estimate_quality_delta(
        self,
        current_model: Optional[str],
        suggested_model: str,
        usage_context: Optional[str],
    ) -> float:
        """Estimate quality change (rough heuristic)."""
        if not current_model:
            return 0

        # Simplified model tiers
        tiers = {
            "gpt-4": 100,
            "gpt-4-turbo": 95,
            "gpt-4o": 90,
            "gpt-4o-mini": 70,
            "gpt-3.5-turbo": 60,
            "claude-opus-4-5-20251101": 100,
            "claude-3-5-sonnet-20241022": 90,
            "claude-3-5-haiku-20241022": 75,
        }

        current_tier = tiers.get(current_model, 80)
        suggested_tier = tiers.get(suggested_model, 80)

        return suggested_tier - current_tier

    def _generate_reasoning(
        self,
        current_model: Optional[str],
        suggested_model: str,
        config: ModelConfig,
        usage_context: Optional[str],
    ) -> str:
        """Generate explanation for recommendation."""
        reasons = []

        if current_model:
            current_config = get_model_config(current_model)
            cost_ratio = (
                config.cost_per_1k_input / current_config.cost_per_1k_input
            )

            if cost_ratio < 0.5:
                reasons.append(
                    f"{suggested_model} costs <50% of {current_model}"
                )
            elif cost_ratio < 0.8:
                reasons.append(
                    f"{suggested_model} is cheaper than {current_model}"
                )

        if usage_context == "simple_qa":
            reasons.append("Fast, cost-effective for simple Q&A")
        elif usage_context == "complex_reasoning":
            reasons.append("Powerful model for complex reasoning")

        if config.max_input_tokens > 100000:
            reasons.append("Large context window for long conversations")

        return ". ".join(reasons) if reasons else "Good balance of cost and capability"
