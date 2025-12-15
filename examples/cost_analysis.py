"""
Cost analysis examples for token-calculator package.
"""

from token_calculator import (
    CostCalculator,
    compare_model_costs,
    search_models,
)


def example_1_basic_cost_calculation():
    """Example 1: Basic cost calculation."""
    print("=" * 60)
    print("Example 1: Basic Cost Calculation")
    print("=" * 60)

    calculator = CostCalculator("gpt-4")

    # Calculate cost for a single request
    input_tokens = 500
    output_tokens = 300

    cost = calculator.calculate_cost(input_tokens, output_tokens)

    print(f"Model: {cost.model_name}")
    print(f"Input tokens: {cost.input_tokens}")
    print(f"Output tokens: {cost.output_tokens}")
    print(f"\nInput cost: ${cost.input_cost:.6f}")
    print(f"Output cost: ${cost.output_cost:.6f}")
    print(f"Total cost: ${cost.total_cost:.6f}")


def example_2_monthly_cost_estimation():
    """Example 2: Estimate monthly costs."""
    print("\n" + "=" * 60)
    print("Example 2: Monthly Cost Estimation")
    print("=" * 60)

    calculator = CostCalculator("gpt-4o")

    # Estimate monthly costs for a production application
    monthly_estimate = calculator.estimate_monthly_cost(
        requests_per_day=1000,
        avg_input_tokens=400,
        avg_output_tokens=250,
    )

    print(f"Usage pattern:")
    print(f"  Requests per day: {monthly_estimate['daily_requests']}")
    print(f"  Avg input tokens: {monthly_estimate['breakdown']['input_tokens_per_request']}")
    print(f"  Avg output tokens: {monthly_estimate['breakdown']['output_tokens_per_request']}")

    print(f"\nCost per request: ${monthly_estimate['cost_per_request']:.6f}")
    print(f"Daily cost: ${monthly_estimate['daily_cost']:.2f}")
    print(f"Weekly cost: ${monthly_estimate['weekly_cost']:.2f}")
    print(f"Monthly cost: ${monthly_estimate['monthly_cost']:.2f}")
    print(f"Yearly cost: ${monthly_estimate['yearly_cost']:.2f}")

    if monthly_estimate['warnings']:
        print("\nWarnings:")
        for warning in monthly_estimate['warnings']:
            print(f"  {warning}")


def example_3_compare_models():
    """Example 3: Compare costs across different models."""
    print("\n" + "=" * 60)
    print("Example 3: Compare Costs Across Models")
    print("=" * 60)

    input_tokens = 1000
    output_tokens = 500

    # Compare specific models
    models_to_compare = [
        "gpt-4",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "claude-3-opus-20240229",
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307",
    ]

    comparisons = compare_model_costs(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model_names=models_to_compare,
    )

    print(f"Comparing costs for {input_tokens} input + {output_tokens} output tokens:\n")
    print(f"{'Model':<40} {'Cost':<12} {'Provider':<12}")
    print("-" * 64)

    for comp in comparisons:
        print(
            f"{comp['model']:<40} ${comp['total_cost']:<11.6f} {comp['provider']:<12}"
        )

    # Calculate savings
    most_expensive = comparisons[-1]['total_cost']
    cheapest = comparisons[0]['total_cost']
    savings = most_expensive - cheapest
    savings_pct = (savings / most_expensive) * 100

    print(f"\nPotential savings: ${savings:.6f} ({savings_pct:.1f}%)")
    print(f"Cheapest model: {comparisons[0]['model']}")
    print(f"Most expensive model: {comparisons[-1]['model']}")


def example_4_cost_savings_from_optimization():
    """Example 4: Calculate savings from token optimization."""
    print("\n" + "=" * 60)
    print("Example 4: Cost Savings from Optimization")
    print("=" * 60)

    calculator = CostCalculator("gpt-4")

    # Scenario: You optimized your prompts
    original_tokens = 1000
    optimized_tokens = 650
    requests_per_month = 50000

    savings = calculator.estimate_cost_savings(
        current_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
        requests_per_month=requests_per_month,
        token_type="input",
    )

    print(f"Optimization scenario:")
    print(f"  Original tokens: {original_tokens}")
    print(f"  Optimized tokens: {optimized_tokens}")
    print(f"  Tokens saved: {savings['tokens_saved_per_request']}")
    print(f"  Reduction: {savings['reduction_percentage']:.1f}%")
    print(f"  Monthly requests: {savings['monthly_requests']:,}")

    print(f"\nCost comparison:")
    print(f"  Current cost per request: ${savings['current_cost_per_request']:.6f}")
    print(f"  Optimized cost per request: ${savings['optimized_cost_per_request']:.6f}")
    print(f"  Savings per request: ${savings['savings_per_request']:.6f}")

    print(f"\nTotal savings:")
    print(f"  Monthly: ${savings['monthly_savings']:.2f}")
    print(f"  Yearly: ${savings['yearly_savings']:.2f}")


def example_5_find_affordable_models():
    """Example 5: Find affordable models for your budget."""
    print("\n" + "=" * 60)
    print("Example 5: Find Affordable Models")
    print("=" * 60)

    # Find models with large context windows and low cost
    affordable_models = search_models(
        min_context=32000,
        max_cost_per_1k_input=0.001,
    )

    print("Affordable models (32k+ context, ≤$0.001 per 1k input tokens):")
    for model in affordable_models:
        print(f"  - {model}")

    # Find models with function calling support
    function_models = search_models(
        supports_function_calling=True,
        max_cost_per_1k_input=0.002,
    )

    print("\nAffordable models with function calling (≤$0.002 per 1k input):")
    for model in function_models[:10]:  # Show first 10
        print(f"  - {model}")


if __name__ == "__main__":
    example_1_basic_cost_calculation()
    example_2_monthly_cost_estimation()
    example_3_compare_models()
    example_4_cost_savings_from_optimization()
    example_5_find_affordable_models()
    print("\n" + "=" * 60)
    print("All cost analysis examples completed!")
    print("=" * 60)
