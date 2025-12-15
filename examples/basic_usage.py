"""
Basic usage examples for token-calculator package.
"""

from token_calculator import (
    count_tokens,
    analyze_prompt,
    TokenCounter,
    list_models,
    ModelProvider,
)


def example_1_simple_token_counting():
    """Example 1: Simple token counting."""
    print("=" * 60)
    print("Example 1: Simple Token Counting")
    print("=" * 60)

    # Count tokens in a simple text
    text = "Hello, how are you today?"
    tokens = count_tokens(text, model_name="gpt-4")
    print(f"Text: {text}")
    print(f"Tokens (GPT-4): {tokens}\n")

    # Compare across models
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3-5-sonnet-20241022"]
    print("Token counts across different models:")
    for model in models:
        try:
            tokens = count_tokens(text, model_name=model)
            print(f"  {model}: {tokens} tokens")
        except Exception as e:
            print(f"  {model}: Error - {e}")


def example_2_message_token_counting():
    """Example 2: Counting tokens in chat messages."""
    print("\n" + "=" * 60)
    print("Example 2: Message Token Counting")
    print("=" * 60)

    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "How do I read a file in Python?"},
        {
            "role": "assistant",
            "content": "You can read a file in Python using the open() function...",
        },
    ]

    counter = TokenCounter("gpt-4")
    breakdown = counter.count_messages(messages)

    print("Token breakdown by role:")
    print(f"  System: {breakdown['system']} tokens")
    print(f"  User: {breakdown['user']} tokens")
    print(f"  Assistant: {breakdown['assistant']} tokens")
    print(f"  Overhead: {breakdown['overhead']} tokens")
    print(f"  Total: {breakdown['total']} tokens")


def example_3_comprehensive_analysis():
    """Example 3: Comprehensive prompt analysis."""
    print("\n" + "=" * 60)
    print("Example 3: Comprehensive Prompt Analysis")
    print("=" * 60)

    prompt = """
    Write a detailed tutorial on how to build a REST API using FastAPI.
    Include examples of:
    - Setting up the project
    - Creating endpoints
    - Request/response models
    - Database integration
    - Authentication
    """

    analysis = analyze_prompt(
        prompt=prompt,
        model_name="gpt-4",
        expected_output_tokens=1000,
    )

    print(f"Input tokens: {analysis['tokens']['input']}")
    print(f"Expected output tokens: {analysis['tokens']['expected_output']}")
    print(f"Total tokens: {analysis['tokens']['total']}")
    print(f"\nContext usage: {analysis['context']['usage_percentage']:.2f}%")
    print(f"Status: {analysis['context']['status']}")
    print(f"Available for output: {analysis['context']['available_for_output']}")
    print(f"\nEstimated cost: {analysis['cost']['formatted']}")
    print(f"  Input cost: ${analysis['cost']['input_cost']:.6f}")
    print(f"  Output cost: ${analysis['cost']['output_cost']:.6f}")

    if analysis['optimization']['suggestions_count'] > 0:
        print(f"\nOptimization suggestions ({analysis['optimization']['suggestions_count']}):")
        for i, suggestion in enumerate(analysis['optimization']['suggestions'], 1):
            print(f"{i}. {suggestion['strategy']}")
            print(f"   {suggestion['description']}")
            print(f"   Potential savings: {suggestion['tokens_saved']} tokens")


def example_4_list_models():
    """Example 4: List and explore available models."""
    print("\n" + "=" * 60)
    print("Example 4: Exploring Available Models")
    print("=" * 60)

    # List all OpenAI models
    openai_models = list_models(provider=ModelProvider.OPENAI)
    print(f"OpenAI models ({len(openai_models)}):")
    for model in openai_models[:5]:  # Show first 5
        print(f"  - {model}")

    # List all Anthropic models
    anthropic_models = list_models(provider=ModelProvider.ANTHROPIC)
    print(f"\nAnthropic models ({len(anthropic_models)}):")
    for model in anthropic_models:
        print(f"  - {model}")


if __name__ == "__main__":
    example_1_simple_token_counting()
    example_2_message_token_counting()
    example_3_comprehensive_analysis()
    example_4_list_models()
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
