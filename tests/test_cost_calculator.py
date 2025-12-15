"""
Tests for cost calculator module.
"""

import pytest
from token_calculator.cost_calculator import (
    CostCalculator,
    calculate_cost,
    compare_model_costs,
)


def test_cost_calculator_init():
    """Test CostCalculator initialization."""
    calc = CostCalculator("gpt-4")
    assert calc.model_name == "gpt-4"


def test_calculate_cost():
    """Test basic cost calculation."""
    calc = CostCalculator("gpt-4")
    cost = calc.calculate_cost(input_tokens=1000, output_tokens=500)

    assert cost.input_tokens == 1000
    assert cost.output_tokens == 500
    assert cost.input_cost > 0
    assert cost.output_cost > 0
    assert cost.total_cost == cost.input_cost + cost.output_cost


def test_estimate_monthly_cost():
    """Test monthly cost estimation."""
    calc = CostCalculator("gpt-4")
    estimate = calc.estimate_monthly_cost(
        requests_per_day=100,
        avg_input_tokens=500,
        avg_output_tokens=300,
    )

    assert estimate["daily_cost"] > 0
    assert estimate["monthly_cost"] > 0
    assert estimate["yearly_cost"] > 0
    assert estimate["monthly_cost"] == estimate["daily_cost"] * 30


def test_compare_models():
    """Test comparing costs across models."""
    calc = CostCalculator("gpt-4")
    comparisons = calc.compare_models(
        input_tokens=1000,
        output_tokens=500,
        model_names=["gpt-4", "gpt-3.5-turbo", "gpt-4o-mini"],
    )

    assert len(comparisons) == 3
    # Should be sorted by cost
    assert comparisons[0]["total_cost"] <= comparisons[1]["total_cost"]


def test_estimate_cost_savings():
    """Test cost savings estimation."""
    calc = CostCalculator("gpt-4")
    savings = calc.estimate_cost_savings(
        current_tokens=1000,
        optimized_tokens=700,
        requests_per_month=10000,
        token_type="input",
    )

    assert savings["tokens_saved_per_request"] == 300
    assert savings["reduction_percentage"] == 30.0
    assert savings["monthly_savings"] > 0


def test_calculate_cost_convenience():
    """Test convenience function."""
    cost = calculate_cost("gpt-4", input_tokens=100, output_tokens=50)
    assert cost.total_cost > 0
