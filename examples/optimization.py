"""
Token optimization examples for token-calculator package.
"""

from token_calculator import TokenOptimizer, optimize_prompt, suggest_optimizations


def example_1_basic_optimization():
    """Example 1: Basic prompt optimization."""
    print("=" * 60)
    print("Example 1: Basic Prompt Optimization")
    print("=" * 60)

    prompt = """
    In order to complete this task, it is important to note that
    you should be very careful and really think about the best
    approach for the purpose of achieving optimal results. Please
    note that you should consider all possible options.
    """

    print(f"Original prompt:\n{prompt}\n")

    # Optimize the prompt
    result = optimize_prompt(prompt, model_name="gpt-4", aggressive=False)

    print(f"Original tokens: {result.original_tokens}")
    print(f"Optimized tokens: {result.optimized_tokens}")
    print(f"Tokens saved: {result.tokens_saved}")
    print(f"Reduction: {result.reduction_percentage:.1f}%")
    print(f"\nOptimized prompt:\n{result.optimized_text}")


def example_2_aggressive_optimization():
    """Example 2: Aggressive optimization."""
    print("\n" + "=" * 60)
    print("Example 2: Aggressive Optimization")
    print("=" * 60)

    prompt = """
    I really need you to very carefully and actually think about
    this problem. It's basically just a simple question, but I
    literally want you to really consider all aspects.
    """

    print(f"Original prompt:\n{prompt}\n")

    optimizer = TokenOptimizer("gpt-4")

    # Normal optimization
    normal_result = optimizer.optimize_text(prompt, aggressive=False)
    print(f"Normal optimization:")
    print(f"  Tokens saved: {normal_result.tokens_saved}")
    print(f"  Reduction: {normal_result.reduction_percentage:.1f}%")

    # Aggressive optimization
    aggressive_result = optimizer.optimize_text(prompt, aggressive=True)
    print(f"\nAggressive optimization:")
    print(f"  Tokens saved: {aggressive_result.tokens_saved}")
    print(f"  Reduction: {aggressive_result.reduction_percentage:.1f}%")
    print(f"\nAggressive result:\n{aggressive_result.optimized_text}")


def example_3_optimization_suggestions():
    """Example 3: Get optimization suggestions."""
    print("\n" + "=" * 60)
    print("Example 3: Optimization Suggestions")
    print("=" * 60)

    prompt = """
    You are a very helpful assistant.


    In order to answer this question, please be very careful.
    Due to the fact that this is important, really think about it.

    ```python
    # This is a very long code example
    def process_data(data):
        # Process the data
        result = []
        for item in data:
            if item is not None:
                processed = item * 2
                result.append(processed)
        return result

    # Call the function
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    processed_data = process_data(data)
    print(processed_data)
    ```

    Please note that you should consider all edge cases.
    """

    suggestions = suggest_optimizations(prompt, model_name="gpt-4")

    print(f"Found {len(suggestions)} optimization opportunities:\n")

    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion.strategy}")
        print(f"   Description: {suggestion.description}")
        print(f"   Tokens saved: {suggestion.estimated_tokens_saved}")
        print(f"   Impact: {suggestion.impact} | Effort: {suggestion.effort}")
        if suggestion.example:
            print(f"   Example: {suggestion.example}")
        print()


def example_4_compare_phrasings():
    """Example 4: Compare different phrasings."""
    print("\n" + "=" * 60)
    print("Example 4: Compare Different Phrasings")
    print("=" * 60)

    optimizer = TokenOptimizer("gpt-4")

    # Different ways to say the same thing
    phrasings = [
        "Could you please explain to me how this algorithm works in detail?",
        "Please explain how this algorithm works in detail",
        "Explain how this algorithm works in detail",
        "Explain this algorithm in detail",
        "Explain this algorithm",
        "How does this algorithm work?",
    ]

    print("Comparing different phrasings (sorted by tokens):\n")

    comparisons = optimizer.compare_phrasings(phrasings)

    for i, comp in enumerate(comparisons, 1):
        print(f"{i}. {comp['tokens']} tokens: \"{comp['text']}\"")
        print(f"   Characters: {comp['characters']}")
        print(f"   Tokens/char ratio: {comp['tokens_per_char']:.3f}\n")

    # Calculate savings
    most_tokens = comparisons[-1]['tokens']
    least_tokens = comparisons[0]['tokens']
    savings = most_tokens - least_tokens
    savings_pct = (savings / most_tokens) * 100

    print(f"Potential savings: {savings} tokens ({savings_pct:.1f}%)")


def example_5_iterative_optimization():
    """Example 5: Iterative optimization with analysis."""
    print("\n" + "=" * 60)
    print("Example 5: Iterative Optimization")
    print("=" * 60)

    prompt = """
    You are an expert in machine learning and artificial intelligence.

    In order to provide the best possible answer, it is important to note that
    you should really consider all aspects of deep learning, neural networks,
    and related technologies.

    Please be very careful and actually think deeply about:
    - Convolutional Neural Networks
    - Recurrent Neural Networks
    - Transformers and Attention Mechanisms
    - Generative Adversarial Networks

    Due to the fact that this is a complex topic, please note that you should
    provide detailed explanations.
    """

    optimizer = TokenOptimizer("gpt-4")

    print(f"Original tokens: {optimizer.token_counter.count_tokens(prompt)}")
    print("\nOptimization iterations:\n")

    current_prompt = prompt
    iteration = 0

    while True:
        iteration += 1

        # Get suggestions
        suggestions = optimizer.suggest_prompt_improvements(current_prompt)

        if not suggestions or iteration > 3:
            break

        print(f"Iteration {iteration}:")
        print(f"  Current tokens: {optimizer.token_counter.count_tokens(current_prompt)}")
        print(f"  Suggestions: {len(suggestions)}")

        # Apply optimization
        result = optimizer.optimize_text(current_prompt, aggressive=(iteration > 1))
        current_prompt = result.optimized_text

        print(f"  After optimization: {result.optimized_tokens} tokens")
        print(f"  Saved this iteration: {result.tokens_saved} tokens\n")

    print(f"Final optimized prompt:\n{current_prompt}")
    print(f"\nFinal token count: {optimizer.token_counter.count_tokens(current_prompt)}")
    original_tokens = optimizer.token_counter.count_tokens(prompt)
    final_tokens = optimizer.token_counter.count_tokens(current_prompt)
    total_saved = original_tokens - final_tokens
    print(f"Total tokens saved: {total_saved} ({total_saved/original_tokens*100:.1f}%)")


if __name__ == "__main__":
    example_1_basic_optimization()
    example_2_aggressive_optimization()
    example_3_optimization_suggestions()
    example_4_compare_phrasings()
    example_5_iterative_optimization()
    print("\n" + "=" * 60)
    print("All optimization examples completed!")
    print("=" * 60)
