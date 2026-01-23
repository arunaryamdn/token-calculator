"""Cost forecasting and budgeting for LLM usage."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .storage import StorageBackend


@dataclass
class Forecast:
    """Cost forecast for a future period.

    Attributes:
        period: Forecast period (monthly, weekly, daily)
        predicted_cost: Predicted cost for the period
        confidence_interval: (low, high) confidence interval
        baseline_cost: Historical baseline cost
        trend: Trend direction (increasing, stable, decreasing)
        factors: Factors influencing the forecast
    """

    period: str
    predicted_cost: float
    confidence_interval: tuple[float, float]
    baseline_cost: float
    trend: str
    factors: List[str]

    def __str__(self) -> str:
        """String representation."""
        trend_emoji = {
            "increasing": "📈",
            "stable": "➡️",
            "decreasing": "📉",
        }
        emoji = trend_emoji.get(self.trend, "❓")

        low, high = self.confidence_interval

        return (
            f"{emoji} {self.period.capitalize()} Forecast:\n"
            f"  Predicted: ${self.predicted_cost:.2f}\n"
            f"  Range: ${low:.2f} - ${high:.2f}\n"
            f"  Baseline: ${self.baseline_cost:.2f}\n"
            f"  Trend: {self.trend}"
        )


@dataclass
class Scenario:
    """Scenario for cost modeling.

    Attributes:
        name: Scenario name
        description: Scenario description
        multipliers: Multipliers for different dimensions
        expected_usage: Expected usage changes
    """

    name: str
    description: str
    multipliers: Dict[str, float]
    expected_usage: Dict[str, float]


@dataclass
class ScenarioResult:
    """Result of scenario modeling.

    Attributes:
        scenario: Original scenario
        current_monthly_cost: Current monthly cost
        projected_monthly_cost: Projected cost under scenario
        cost_delta: Change in cost
        cost_delta_pct: Percentage change in cost
        breakdown: Cost breakdown by dimension
    """

    scenario: Scenario
    current_monthly_cost: float
    projected_monthly_cost: float
    cost_delta: float
    cost_delta_pct: float
    breakdown: Dict[str, float]

    def __str__(self) -> str:
        """String representation."""
        direction = "📈" if self.cost_delta > 0 else "📉"

        return (
            f"Scenario: {self.scenario.name}\n"
            f"  {self.scenario.description}\n"
            f"  Current: ${self.current_monthly_cost:.2f}/month\n"
            f"  Projected: ${self.projected_monthly_cost:.2f}/month\n"
            f"  {direction} Change: ${abs(self.cost_delta):.2f} ({abs(self.cost_delta_pct):.1f}%)"
        )


@dataclass
class BudgetStatus:
    """Budget status report.

    Attributes:
        budget_amount: Total budget
        spent: Amount spent
        remaining: Amount remaining
        remaining_pct: Percentage remaining
        period: Budget period
        days_remaining: Days remaining in period
        projected_overage: Projected overage (if any)
        on_track: Whether spending is on track
    """

    budget_amount: float
    spent: float
    remaining: float
    remaining_pct: float
    period: str
    days_remaining: int
    projected_overage: float
    on_track: bool

    def __str__(self) -> str:
        """String representation."""
        status_emoji = "✅" if self.on_track else "⚠️"

        lines = [
            f"{status_emoji} Budget Status ({self.period}):",
            f"  Budget: ${self.budget_amount:.2f}",
            f"  Spent: ${self.spent:.2f}",
            f"  Remaining: ${self.remaining:.2f} ({self.remaining_pct:.1f}%)",
            f"  Days Remaining: {self.days_remaining}",
        ]

        if not self.on_track and self.projected_overage > 0:
            lines.append(f"  ⚠️  Projected Overage: ${self.projected_overage:.2f}")

        return "\n".join(lines)


class CostForecaster:
    """Forecast future costs based on historical data.

    Analyzes historical usage patterns to predict future costs,
    enabling budget planning and capacity forecasting.

    Args:
        storage: Storage backend with historical data

    Example:
        >>> from token_calculator import CostForecaster, create_storage
        >>> forecaster = CostForecaster(
        ...     storage=create_storage("sqlite", db_path="costs.db")
        ... )
        >>> forecast = forecaster.forecast_monthly(agent_id="rag-agent")
        >>> print(forecast)
    """

    def __init__(self, storage: StorageBackend):
        """Initialize forecaster.

        Args:
            storage: Storage backend with historical data
        """
        self.storage = storage

    def forecast_monthly(
        self,
        agent_id: Optional[str] = None,
        lookback_days: int = 30,
    ) -> Forecast:
        """Forecast next month's costs.

        Args:
            agent_id: Optional agent ID to forecast for
            lookback_days: Days of historical data to use

        Returns:
            Forecast for next month

        Example:
            >>> forecast = forecaster.forecast_monthly(
            ...     agent_id="customer-support",
            ...     lookback_days=30
            ... )
            >>> print(f"Predicted: ${forecast.predicted_cost:.2f}")
        """
        now = datetime.now()
        start_time = now - timedelta(days=lookback_days)

        # Get historical costs
        filters = {"agent_id": agent_id} if agent_id else None
        cost_data = self.storage.aggregate(
            metric="cost",
            filters=filters,
            start_time=start_time,
            end_time=now,
        )

        total_historical_cost = cost_data.get("total", 0)

        # Calculate daily average
        daily_avg = total_historical_cost / lookback_days

        # Forecast next 30 days
        predicted_cost = daily_avg * 30

        # Calculate trend (compare first half vs second half)
        mid_point = start_time + timedelta(days=lookback_days // 2)

        first_half_cost = self.storage.aggregate(
            metric="cost",
            filters=filters,
            start_time=start_time,
            end_time=mid_point,
        ).get("total", 0)

        second_half_cost = self.storage.aggregate(
            metric="cost",
            filters=filters,
            start_time=mid_point,
            end_time=now,
        ).get("total", 0)

        # Determine trend
        if second_half_cost > first_half_cost * 1.2:
            trend = "increasing"
            # Adjust prediction upward
            predicted_cost *= 1.1
        elif second_half_cost < first_half_cost * 0.8:
            trend = "decreasing"
            # Adjust prediction downward
            predicted_cost *= 0.9
        else:
            trend = "stable"

        # Calculate confidence interval (±20%)
        confidence_interval = (
            predicted_cost * 0.8,
            predicted_cost * 1.2,
        )

        # Identify factors
        factors = []
        if trend == "increasing":
            factors.append("Usage trending upward")
        elif trend == "decreasing":
            factors.append("Usage trending downward")

        if total_historical_cost < 10:
            factors.append("Limited historical data - low confidence")

        return Forecast(
            period="monthly",
            predicted_cost=predicted_cost,
            confidence_interval=confidence_interval,
            baseline_cost=total_historical_cost,
            trend=trend,
            factors=factors,
        )

    def scenario_model(
        self,
        scenario: Scenario,
        lookback_days: int = 30,
    ) -> ScenarioResult:
        """Model a what-if scenario.

        Args:
            scenario: Scenario to model
            lookback_days: Days of historical data to use

        Returns:
            Scenario result with projected costs

        Example:
            >>> scenario = Scenario(
            ...     name="10x growth",
            ...     description="Model 10x user growth",
            ...     multipliers={"user_count": 10.0},
            ...     expected_usage={}
            ... )
            >>> result = forecaster.scenario_model(scenario)
            >>> print(result)
        """
        # Get current monthly cost
        now = datetime.now()
        start_time = now - timedelta(days=lookback_days)

        current_cost = self.storage.aggregate(
            metric="cost",
            start_time=start_time,
            end_time=now,
        ).get("total", 0)

        current_monthly = (current_cost / lookback_days) * 30

        # Apply scenario multipliers
        # Simple model: multiply cost by scenario factors
        multiplier = 1.0
        for key, value in scenario.multipliers.items():
            multiplier *= value

        projected_monthly = current_monthly * multiplier

        # Calculate delta
        cost_delta = projected_monthly - current_monthly
        cost_delta_pct = (
            (cost_delta / current_monthly * 100) if current_monthly > 0 else 0
        )

        # Get breakdown by agent
        breakdown_data = self.storage.aggregate(
            metric="cost",
            group_by=["agent_id"],
            start_time=start_time,
            end_time=now,
        )

        breakdown = {}
        for (agent_id,), cost in breakdown_data.items():
            monthly_cost = (cost / lookback_days) * 30
            breakdown[agent_id] = monthly_cost * multiplier

        return ScenarioResult(
            scenario=scenario,
            current_monthly_cost=current_monthly,
            projected_monthly_cost=projected_monthly,
            cost_delta=cost_delta,
            cost_delta_pct=cost_delta_pct,
            breakdown=breakdown,
        )


class BudgetTracker:
    """Track budgets and spending.

    Monitors spending against budgets, provides remaining budget visibility,
    and alerts when approaching limits.

    Args:
        storage: Storage backend

    Example:
        >>> from token_calculator import BudgetTracker, create_storage
        >>> tracker = BudgetTracker(
        ...     storage=create_storage("sqlite", db_path="costs.db")
        ... )
        >>> tracker.set_budget(amount=1000, period="monthly")
        >>> status = tracker.get_status()
        >>> print(status)
    """

    def __init__(self, storage: StorageBackend):
        """Initialize budget tracker.

        Args:
            storage: Storage backend
        """
        self.storage = storage
        self.budgets: Dict[str, Dict] = {}

    def set_budget(
        self,
        amount: float,
        period: str = "monthly",
        filters: Optional[Dict[str, str]] = None,
        name: str = "default",
    ):
        """Set a budget.

        Args:
            amount: Budget amount
            period: Budget period (monthly, weekly, daily)
            filters: Optional filters (e.g., {"agent_id": "my-agent"})
            name: Budget name

        Example:
            >>> tracker.set_budget(
            ...     amount=1000,
            ...     period="monthly",
            ...     filters={"environment": "production"},
            ...     name="production-budget"
            ... )
        """
        now = datetime.now()

        if period == "monthly":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of month
            if now.month == 12:
                end_date = now.replace(
                    year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                end_date = now.replace(
                    month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
                )
        elif period == "weekly":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        elif period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        else:
            raise ValueError(f"Unknown period: {period}")

        self.budgets[name] = {
            "amount": amount,
            "period": period,
            "filters": filters or {},
            "start_date": start_date,
            "end_date": end_date,
        }

    def get_status(self, name: str = "default") -> BudgetStatus:
        """Get budget status.

        Args:
            name: Budget name

        Returns:
            BudgetStatus with current status

        Example:
            >>> status = tracker.get_status("production-budget")
            >>> if not status.on_track:
            ...     print("⚠️  Budget overage projected!")
        """
        if name not in self.budgets:
            raise ValueError(f"Budget not found: {name}")

        budget = self.budgets[name]

        # Get spending
        spent_data = self.storage.aggregate(
            metric="cost",
            filters=budget["filters"],
            start_time=budget["start_date"],
            end_time=datetime.now(),
        )

        spent = spent_data.get("total", 0)
        remaining = budget["amount"] - spent
        remaining_pct = (remaining / budget["amount"] * 100) if budget["amount"] > 0 else 0

        # Calculate days remaining
        now = datetime.now()
        days_remaining = (budget["end_date"] - now).days

        # Project overage
        days_elapsed = (now - budget["start_date"]).days
        if days_elapsed > 0:
            daily_rate = spent / days_elapsed
            projected_total = daily_rate * (days_elapsed + days_remaining)
            projected_overage = max(0, projected_total - budget["amount"])
        else:
            projected_overage = 0

        # Check if on track (remaining budget > remaining days ratio)
        total_days = (budget["end_date"] - budget["start_date"]).days
        expected_spent_pct = (days_elapsed / total_days * 100) if total_days > 0 else 0
        actual_spent_pct = (spent / budget["amount"] * 100) if budget["amount"] > 0 else 0

        on_track = actual_spent_pct <= expected_spent_pct * 1.1  # 10% tolerance

        return BudgetStatus(
            budget_amount=budget["amount"],
            spent=spent,
            remaining=remaining,
            remaining_pct=remaining_pct,
            period=budget["period"],
            days_remaining=days_remaining,
            projected_overage=projected_overage,
            on_track=on_track,
        )

    def check_overage(self, name: str = "default") -> bool:
        """Check if over budget.

        Args:
            name: Budget name

        Returns:
            True if over budget

        Example:
            >>> if tracker.check_overage():
            ...     send_alert("Budget exceeded!")
        """
        status = self.get_status(name)
        return status.remaining < 0
