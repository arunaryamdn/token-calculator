"""
Conversation management examples for token-calculator package.
"""

from token_calculator import ConversationManager


def example_1_basic_conversation():
    """Example 1: Basic conversation tracking."""
    print("=" * 60)
    print("Example 1: Basic Conversation Tracking")
    print("=" * 60)

    # Initialize conversation manager
    manager = ConversationManager(
        model_name="gpt-4",
        system_message="You are a helpful Python programming assistant.",
    )

    # Simulate a conversation
    turns = [
        (
            "How do I read a CSV file in Python?",
            "You can read a CSV file in Python using the csv module or pandas library. Here's an example using pandas: import pandas as pd; df = pd.read_csv('file.csv')",
        ),
        (
            "What about writing to a CSV file?",
            "To write to a CSV file with pandas, use df.to_csv('output.csv', index=False). With the csv module, you can use csv.writer().",
        ),
        (
            "Can you show me error handling for file operations?",
            "Sure! Use try-except blocks: try: with open('file.csv', 'r') as f: # read file except FileNotFoundError: print('File not found') except PermissionError: print('Permission denied')",
        ),
    ]

    for user_msg, assistant_msg in turns:
        turn = manager.add_turn(user_msg, assistant_msg)
        print(f"\nTurn added:")
        print(f"  User tokens: {turn.user_tokens}")
        print(f"  Assistant tokens: {turn.assistant_tokens}")
        print(f"  Cost: ${turn.cost:.6f}")

    # Get conversation statistics
    stats = manager.get_stats()
    print(f"\n{'='*60}")
    print("Conversation Statistics:")
    print(f"{'='*60}")
    print(f"Total turns: {stats.total_turns}")
    print(f"Total tokens: {stats.total_tokens}")
    print(f"Total cost: ${stats.total_cost:.6f}")
    print(f"Context usage: {stats.context_usage_percentage:.2f}%")
    print(f"Status: {stats.context_status.value}")
    print(f"Estimated turns remaining: {stats.estimated_turns_remaining}")


def example_2_rag_conversation():
    """Example 2: Conversation with RAG context."""
    print("\n" + "=" * 60)
    print("Example 2: Conversation with RAG Context")
    print("=" * 60)

    # RAG context (e.g., from documentation)
    rag_context = """
    FastAPI Documentation Summary:
    - FastAPI is a modern web framework for building APIs
    - It uses Python type hints for validation
    - Built on Starlette and Pydantic
    - Supports async/await
    - Automatic API documentation
    """

    manager = ConversationManager(
        model_name="gpt-4",
        system_message="You are a FastAPI expert. Use the provided documentation context.",
        rag_context=rag_context,
    )

    print(f"Fixed overhead (system + RAG): {manager.fixed_overhead} tokens")

    # Add conversation turns
    manager.add_turn(
        "How do I create a basic FastAPI endpoint?",
        "Based on the documentation, you create an endpoint using @app.get() decorator...",
    )

    # Get context breakdown
    breakdown = manager.get_context_breakdown()
    print(f"\nContext breakdown:")
    print(f"  Total tokens: {breakdown['total_tokens']}")
    print(f"  Usage: {breakdown['usage_percentage']:.2f}%")
    print(f"  Status: {breakdown['status']}")
    print(f"  Available for output: {breakdown['available_for_output']}")

    print(f"\nDetailed breakdown:")
    for key, value in breakdown['breakdown'].items():
        print(f"  {key}: {value} tokens")


def example_3_managing_context_limits():
    """Example 3: Managing context limits."""
    print("\n" + "=" * 60)
    print("Example 3: Managing Context Limits")
    print("=" * 60)

    manager = ConversationManager(
        model_name="gpt-3.5-turbo",  # Smaller context window
        system_message="You are a helpful assistant.",
    )

    # Simulate many turns
    for i in range(10):
        manager.add_turn(
            f"This is question number {i+1} about Python programming.",
            f"This is a detailed answer to question {i+1} with lots of information and code examples that consume many tokens.",
        )

    stats = manager.get_stats()
    print(f"After 10 turns:")
    print(f"  Total tokens: {stats.total_tokens}")
    print(f"  Context usage: {stats.context_usage_percentage:.2f}%")
    print(f"  Estimated turns remaining: {stats.estimated_turns_remaining}")

    # Check if we can add more turns
    can_add = manager.can_add_turn(
        estimated_user_tokens=50,
        estimated_assistant_tokens=200,
    )

    print(f"\nCan add more turns? {can_add['can_add']}")
    print(f"Recommendation: {can_add['recommendation']}")

    # If context is getting full, summarize
    if stats.context_usage_percentage > 70:
        print("\nContext usage high - summarizing conversation...")
        summary_result = manager.summarize_conversation(keep_recent_turns=3)

        print(f"Summarization results:")
        print(f"  Original turns summarized: {summary_result['original_turns']}")
        print(f"  Kept recent turns: {summary_result['kept_turns']}")
        print(f"  Original tokens: {summary_result['original_tokens']}")
        print(f"  Summary tokens: {summary_result['summary_tokens']}")
        print(f"  Tokens saved: {summary_result['tokens_saved']}")

        # Check new stats
        new_stats = manager.get_stats()
        print(f"\nAfter summarization:")
        print(f"  Context usage: {new_stats.context_usage_percentage:.2f}%")
        print(f"  Estimated turns remaining: {new_stats.estimated_turns_remaining}")


def example_4_conversation_export():
    """Example 4: Export conversation for analysis."""
    print("\n" + "=" * 60)
    print("Example 4: Export Conversation")
    print("=" * 60)

    manager = ConversationManager(
        model_name="gpt-4",
        system_message="You are a coding assistant.",
    )

    # Add some turns
    manager.add_turn(
        "Explain list comprehensions",
        "List comprehensions provide a concise way to create lists...",
    )
    manager.add_turn(
        "Show me an example",
        "Here's an example: squares = [x**2 for x in range(10)]",
    )

    # Export conversation
    exported = manager.export_conversation()

    print(f"Exported conversation:")
    print(f"  Model: {exported['model_name']}")
    print(f"  Total messages: {len(exported['messages'])}")
    print(f"  Total turns: {len(exported['turns'])}")
    print(f"  Fixed overhead: {exported['fixed_overhead']} tokens")

    print(f"\nTurn details:")
    for i, turn in enumerate(exported['turns'], 1):
        print(f"  Turn {i}:")
        print(f"    Cost: ${turn['cost']:.6f}")
        print(f"    Total tokens: {turn['total_tokens']}")


if __name__ == "__main__":
    example_1_basic_conversation()
    example_2_rag_conversation()
    example_3_managing_context_limits()
    example_4_conversation_export()
    print("\n" + "=" * 60)
    print("All conversation management examples completed!")
    print("=" * 60)
