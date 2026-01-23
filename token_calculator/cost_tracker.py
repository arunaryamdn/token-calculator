"""Cost tracking with custom labels and time-series analysis."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .cost_calculator import CostCalculator
from .models import get_model_config
from .storage import InMemoryStorage, StorageBackend, TrackingEvent


@dataclass
class CostRecord:
    """Result of tracking a single LLM call.

    Attributes:
        event_id: Unique event identifier
        timestamp: When the call occurred
        model: Model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        input_cost: Cost of input tokens
        output_cost: Cost of output tokens
        total_cost: Total cost
        labels: Custom labels
    """

    event_id: str
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    labels: Dict[str, str]


@dataclass
class CostReport:
    """Cost report with aggregated metrics.

    Attributes:
        total_cost: Total cost across all events
        total_input_tokens: Total input tokens
        total_output_tokens: Total output tokens
        total_calls: Total number of LLM calls
        breakdown: Cost breakdown by dimensions (if group_by used)
        time_range: Time range of the report
        filters: Filters applied to generate this report
    """

    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    total_calls: int
    breakdown: Optional[Dict[Tuple[str, ...], float]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    filters: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """String representation of cost report."""
        lines = [
            f"Cost Report ({self.total_calls} calls)",
            f"  Total Cost: ${self.total_cost:.4f}",
            f"  Input Tokens: {self.total_input_tokens:,}",
            f"  Output Tokens: {self.total_output_tokens:,}",
        ]

        if self.time_range:
            start, end = self.time_range
            lines.append(
                f"  Time Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
            )

        if self.breakdown:
            lines.append("\n  Breakdown:")
            for key, cost in sorted(
                self.breakdown.items(), key=lambda x: x[1], reverse=True
            ):
                key_str = " | ".join(str(k) for k in key)
                lines.append(f"    {key_str}: ${cost:.4f}")

        return "\n".join(lines)


@dataclass
class Anomaly:
    """Cost anomaly detection result.

    Attributes:
        dimension: Dimension where anomaly occurred (e.g., agent_id, model)
        value: Value of the dimension (e.g., "agent-1", "gpt-4")
        current_cost: Current cost
        baseline_cost: Expected baseline cost
        deviation: How many times higher than baseline (e.g., 2.5 = 250% of baseline)
        timestamp: When anomaly was detected
    """

    dimension: str
    value: str
    current_cost: float
    baseline_cost: float
    deviation: float
    timestamp: datetime

    def __str__(self) -> str:
        """String representation."""
        return (
            f"🚨 Anomaly detected: {self.dimension}={self.value}\n"
            f"   Current: ${self.current_cost:.2f} | "
            f"   Baseline: ${self.baseline_cost:.2f} | "
            f"   Deviation: {self.deviation:.1f}x"
        )


@dataclass
class Recommendation:
    """Cost optimization recommendation.

    Attributes:
        title: Short recommendation title
        description: Detailed description
        potential_savings: Estimated monthly savings
        confidence: Confidence level (0-1)
        priority: Priority (high, medium, low)
        actionable: Specific action to take
    """

    title: str
    description: str
    potential_savings: float
    confidence: float
    priority: str
    actionable: str

    def __str__(self) -> str:
        """String representation."""
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        emoji = priority_emoji.get(self.priority, "⚪")

        return (
            f"{emoji} {self.title}\n"
            f"   Potential savings: ${self.potential_savings:.2f}/month\n"
            f"   Confidence: {self.confidence*100:.0f}%\n"
            f"   Action: {self.actionable}"
        )


class CostTracker:
    """Track LLM costs over time with custom labels.

    Provides comprehensive cost tracking with:
    - Custom labels for multi-dimensional analysis
    - Time-series cost tracking
    - Cost anomaly detection
    - Optimization recommendations
    - Cost aggregation and reporting

    Args:
        storage: Storage backend for persisting events
        default_labels: Default labels to apply to all tracked calls

    Example:
        >>> from token_calculator import CostTracker, create_storage
        >>> tracker = CostTracker(
        ...     storage=create_storage("sqlite", db_path="costs.db"),
        ...     default_labels={"environment": "production", "team": "ai"}
        ... )
        >>> record = tracker.track_call(
        ...     model="gpt-4",
        ...     input_tokens=1000,
        ...     output_tokens=500,
        ...     agent_id="customer-support",
        ...     user_id="user-123"
        ... )
        >>> report = tracker.get_costs(
        ...     start_date="2024-01-01",
        ...     group_by=["agent_id", "model"]
        ... )
        >>> print(report)
    """

    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
        default_labels: Optional[Dict[str, str]] = None,
    ):
        """Initialize cost tracker.

        Args:
            storage: Storage backend (defaults to in-memory)
            default_labels: Default labels to apply to all calls
        """
        self.storage = storage or InMemoryStorage()
        self.default_labels = default_labels or {}

    def track_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        **labels,
    ) -> CostRecord:
        """Track a single LLM call with custom labels.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            **labels: Custom labels (agent_id="agent-1", user_id="user-123", etc.)

        Returns:
            CostRecord with cost details

        Example:
            >>> record = tracker.track_call(
            ...     model="gpt-4",
            ...     input_tokens=1000,
            ...     output_tokens=500,
            ...     agent_id="rag-agent",
            ...     environment="production"
            ... )
            >>> print(f"Cost: ${record.total_cost:.4f}")
        """
        # Calculate cost
        calculator = CostCalculator(model)
        breakdown = calculator.calculate_cost(input_tokens, output_tokens)

        # Merge default labels with call-specific labels
        all_labels = {**self.default_labels, **labels}

        # Create tracking event
        event = TrackingEvent.create_llm_call(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=breakdown.total_cost,
            **all_labels,
        )

        # Save to storage
        self.storage.save_event(event)

        # Return cost record
        return CostRecord(
            event_id=event.event_id,
            timestamp=event.timestamp,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=breakdown.input_cost,
            output_cost=breakdown.output_cost,
            total_cost=breakdown.total_cost,
            labels=all_labels,
        )

    def get_costs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
    ) -> CostReport:
        """Get cost report for a time period with optional grouping.

        Args:
            start_date: Start date (formats: "YYYY-MM-DD", "yesterday", "this-week", "this-month")
            end_date: End date (formats: "YYYY-MM-DD", "today", "now")
            group_by: Dimensions to group by (e.g., ["agent_id", "model"])
            filters: Filter conditions (e.g., {"environment": "production"})

        Returns:
            CostReport with aggregated metrics

        Example:
            >>> # Get this month's costs by agent and model
            >>> report = tracker.get_costs(
            ...     start_date="this-month",
            ...     group_by=["agent_id", "model"],
            ...     filters={"environment": "production"}
            ... )
            >>> print(report)
        """
        # Parse dates
        start_time = self._parse_date(start_date) if start_date else None
        end_time = self._parse_date(end_date) if end_date else None

        # Get aggregated costs
        cost_data = self.storage.aggregate(
            metric="cost",
            group_by=group_by,
            filters=filters,
            start_time=start_time,
            end_time=end_time,
        )

        # Get token counts
        input_tokens_data = self.storage.aggregate(
            metric="input_tokens",
            group_by=None,
            filters=filters,
            start_time=start_time,
            end_time=end_time,
        )

        output_tokens_data = self.storage.aggregate(
            metric="output_tokens",
            group_by=None,
            filters=filters,
            start_time=start_time,
            end_time=end_time,
        )

        count_data = self.storage.aggregate(
            metric="count",
            group_by=None,
            filters=filters,
            start_time=start_time,
            end_time=end_time,
        )

        # Build report
        if group_by:
            total_cost = sum(cost_data.values())
            breakdown = cost_data
        else:
            total_cost = cost_data.get("total", 0)
            breakdown = None

        return CostReport(
            total_cost=total_cost,
            total_input_tokens=input_tokens_data.get("total", 0),
            total_output_tokens=output_tokens_data.get("total", 0),
            total_calls=count_data.get("total", 0),
            breakdown=breakdown,
            time_range=(start_time, end_time) if start_time and end_time else None,
            filters=filters,
        )

    def detect_anomalies(
        self,
        dimension: str = "agent_id",
        threshold: float = 2.0,
        lookback_days: int = 7,
        current_window_hours: int = 1,
    ) -> List[Anomaly]:
        """Detect cost anomalies by comparing current costs to baseline.

        Args:
            dimension: Dimension to check (e.g., "agent_id", "model")
            threshold: Deviation threshold (e.g., 2.0 = 200% of baseline)
            lookback_days: Days of historical data to use for baseline
            current_window_hours: Hours of recent data to check for anomalies

        Returns:
            List of detected anomalies

        Example:
            >>> anomalies = tracker.detect_anomalies(
            ...     dimension="agent_id",
            ...     threshold=2.0,  # Alert if 2x normal cost
            ...     lookback_days=7
            ... )
            >>> for anomaly in anomalies:
            ...     print(anomaly)
        """
        now = datetime.now()
        baseline_start = now - timedelta(days=lookback_days)
        current_start = now - timedelta(hours=current_window_hours)

        # Get baseline costs
        baseline_costs = self.storage.aggregate(
            metric="cost",
            group_by=[dimension],
            start_time=baseline_start,
            end_time=current_start,
        )

        # Get current costs
        current_costs = self.storage.aggregate(
            metric="cost",
            group_by=[dimension],
            start_time=current_start,
            end_time=now,
        )

        # Calculate baseline averages (cost per hour)
        baseline_hours = (current_start - baseline_start).total_seconds() / 3600
        baseline_avg = {
            key: cost / baseline_hours for key, cost in baseline_costs.items()
        }

        # Detect anomalies
        anomalies = []
        for key, current_cost in current_costs.items():
            if key not in baseline_avg:
                continue  # New dimension, skip

            baseline = baseline_avg[key] * current_window_hours
            if baseline == 0:
                continue  # Avoid division by zero

            deviation = current_cost / baseline

            if deviation >= threshold:
                anomalies.append(
                    Anomaly(
                        dimension=dimension,
                        value=key[0],  # First element of tuple
                        current_cost=current_cost,
                        baseline_cost=baseline,
                        deviation=deviation,
                        timestamp=now,
                    )
                )

        return sorted(anomalies, key=lambda a: a.deviation, reverse=True)

    def get_recommendations(
        self,
        top_k: int = 5,
        lookback_days: int = 30,
    ) -> List[Recommendation]:
        """Get cost optimization recommendations.

        Args:
            top_k: Number of top recommendations to return
            lookback_days: Days of historical data to analyze

        Returns:
            List of recommendations sorted by potential savings

        Example:
            >>> recommendations = tracker.get_recommendations(top_k=5)
            >>> for rec in recommendations:
            ...     print(rec)
        """
        now = datetime.now()
        start_time = now - timedelta(days=lookback_days)

        recommendations = []

        # Recommendation 1: Expensive models that could be downgraded
        model_costs = self.storage.aggregate(
            metric="cost",
            group_by=["model"],
            start_time=start_time,
        )

        expensive_models = {
            "gpt-4": "gpt-4o",
            "gpt-4-turbo": "gpt-4o",
            "claude-3-opus-20240229": "claude-3-5-sonnet-20241022",
        }

        for (model,), cost in model_costs.items():
            if model in expensive_models:
                cheaper_model = expensive_models[model]
                model_config = get_model_config(model)
                cheaper_config = get_model_config(cheaper_model)

                # Estimate savings (rough approximation)
                savings_ratio = 1 - (
                    cheaper_config.cost_per_1k_input / model_config.cost_per_1k_input
                )
                monthly_savings = (cost / lookback_days) * 30 * savings_ratio

                recommendations.append(
                    Recommendation(
                        title=f"Consider {cheaper_model} instead of {model}",
                        description=f"{cheaper_model} offers similar capabilities at lower cost",
                        potential_savings=monthly_savings,
                        confidence=0.7,
                        priority="high" if monthly_savings > 100 else "medium",
                        actionable=f"Test {cheaper_model} with A/B testing to validate quality",
                    )
                )

        # Recommendation 2: High-volume agents (caching opportunities)
        agent_costs = self.storage.aggregate(
            metric="cost",
            group_by=["agent_id"],
            start_time=start_time,
        )

        for (agent_id,), cost in sorted(
            agent_costs.items(), key=lambda x: x[1], reverse=True
        )[:3]:
            monthly_cost = (cost / lookback_days) * 30
            if monthly_cost > 50:  # Only recommend if significant cost
                # Estimate 10-20% savings from caching
                savings = monthly_cost * 0.15

                recommendations.append(
                    Recommendation(
                        title=f"Enable prompt caching for {agent_id}",
                        description="High-volume agent could benefit from prompt caching",
                        potential_savings=savings,
                        confidence=0.6,
                        priority="medium" if savings > 50 else "low",
                        actionable="Implement prompt caching for system prompts and RAG context",
                    )
                )

        # Sort by potential savings and return top_k
        recommendations.sort(key=lambda r: r.potential_savings, reverse=True)
        return recommendations[:top_k]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime.

        Supports:
        - ISO format: "2024-01-01"
        - Relative: "today", "yesterday", "this-week", "this-month"
        """
        now = datetime.now()

        if date_str == "now" or date_str == "today":
            return now
        elif date_str == "yesterday":
            return now - timedelta(days=1)
        elif date_str == "this-week":
            return now - timedelta(days=now.weekday())
        elif date_str == "this-month":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Try to parse as ISO date
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {date_str}. "
                    "Use YYYY-MM-DD or today/yesterday/this-week/this-month"
                )
