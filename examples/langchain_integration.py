"""
LangChain Integration Example

Shows how to add Token Calculator tracking to existing LangChain applications
with minimal code changes.
"""

# Note: This example requires LangChain to be installed
# pip install langchain langchain-openai

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import StrOutputParser
except ImportError:
    print("⚠️  LangChain not installed. Install with: pip install langchain langchain-openai")
    exit(1)

from token_calculator import (
    CostTracker,
    create_storage,
)
from token_calculator.integrations.langchain import TokenCalculatorCallback


def basic_integration():
    """Basic LangChain integration - track all LLM calls."""
    print("=" * 60)
    print("BASIC LANGCHAIN INTEGRATION")
    print("=" * 60)

    # 1. Create a cost tracker
    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="langchain_costs.db"),
        default_labels={
            "environment": "development",
            "application": "qa-bot"
        }
    )

    # 2. Create callback
    callback = TokenCalculatorCallback(
        tracker=tracker,
        agent_id="qa-agent",
        version="v1.0"
    )

    # 3. Use with LangChain (just add callbacks parameter!)
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        callbacks=[callback]  # ← This is all you need!
    )

    # Now use LangChain normally - tracking happens automatically
    print("\n📝 Asking a question...")
    response = llm.invoke("What is the capital of France?")
    print(f"Response: {response.content}")

    # Check costs
    print("\n💰 Cost Report:")
    report = tracker.get_costs(start_date="today")
    print(report)


def chain_integration():
    """Track costs in LangChain chains."""
    print("\n" + "=" * 60)
    print("LANGCHAIN CHAIN INTEGRATION")
    print("=" * 60)

    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="langchain_costs.db")
    )

    callback = TokenCalculatorCallback(
        tracker=tracker,
        agent_id="translation-chain"
    )

    # Create a translation chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a translator. Translate to {target_language}."),
        ("user", "{text}")
    ])

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        callbacks=[callback]
    )

    chain = prompt | llm | StrOutputParser()

    # Run the chain
    print("\n🔄 Running translation chain...")
    result = chain.invoke({
        "target_language": "Spanish",
        "text": "Hello, how are you today?"
    })

    print(f"Translation: {result}")

    # Check costs by agent
    print("\n💰 Translation Chain Costs:")
    report = tracker.get_costs(
        start_date="today",
        group_by=["agent_id"]
    )
    print(report)


def multi_agent_rag_system():
    """Track a multi-agent RAG system with LangChain."""
    print("\n" + "=" * 60)
    print("MULTI-AGENT RAG SYSTEM")
    print("=" * 60)

    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="langchain_costs.db")
    )

    # Router agent
    print("\n🤖 Router Agent:")
    router_callback = TokenCalculatorCallback(
        tracker=tracker,
        agent_id="router",
        stage="routing"
    )

    router_llm = ChatOpenAI(
        model="gpt-4o-mini",
        callbacks=[router_callback]
    )

    route_prompt = ChatPromptTemplate.from_template(
        "Route this query to the right agent (qa/support/sales): {query}"
    )

    router_chain = route_prompt | router_llm | StrOutputParser()

    query = "How do I reset my password?"
    route = router_chain.invoke({"query": query})
    print(f"Routed to: {route}")

    # QA agent (simulated)
    print("\n🤖 QA Agent:")
    qa_callback = TokenCalculatorCallback(
        tracker=tracker,
        agent_id="qa-agent",
        stage="retrieval"
    )

    qa_llm = ChatOpenAI(
        model="gpt-4o",
        callbacks=[qa_callback]
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful QA agent. Context: {context}"),
        ("user", "{query}")
    ])

    qa_chain = qa_prompt | qa_llm | StrOutputParser()

    # Simulate RAG retrieval
    context = "Password reset: Go to Settings > Security > Reset Password"
    answer = qa_chain.invoke({
        "context": context,
        "query": query
    })

    print(f"Answer: {answer}")

    # Cost breakdown by agent
    print("\n💰 Cost Breakdown by Agent:")
    report = tracker.get_costs(
        start_date="today",
        group_by=["agent_id", "stage"]
    )
    print(report)


def production_monitoring():
    """Production setup with budgets and alerts."""
    print("\n" + "=" * 60)
    print("PRODUCTION MONITORING SETUP")
    print("=" * 60)

    from token_calculator import AlertManager, BudgetTracker, AlertRule

    # Setup tracker
    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="production.db"),
        default_labels={"environment": "production"}
    )

    # Setup alerts
    alerts = AlertManager()

    alerts.add_rule(AlertRule(
        name="high-cost-call",
        condition=lambda e: e.cost > 0.50,
        severity="warning",
        message_template="High cost call: ${cost:.2f} for {agent_id}",
        channels=["console"]
    ))

    # Setup budget
    budget = BudgetTracker(storage=tracker.storage)
    budget.set_budget(
        amount=1000,  # $1000/month
        period="monthly",
        name="production-budget"
    )

    # Create callback with alert checking
    class MonitoredCallback(TokenCalculatorCallback):
        def __init__(self, *args, alerts=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.alerts = alerts

        def on_llm_end(self, response, *, run_id, **kwargs):
            # Track as normal
            super().on_llm_end(response, run_id=run_id, **kwargs)

            # Check alerts
            if self.alerts and hasattr(self, 'last_event'):
                triggered = self.alerts.check_event(self.last_event)
                for alert in triggered:
                    print(f"\n{alert}")

    callback = MonitoredCallback(
        tracker=tracker,
        alerts=alerts,
        agent_id="production-agent"
    )

    llm = ChatOpenAI(
        model="gpt-4",
        callbacks=[callback]
    )

    print("\n📝 Running production query...")
    result = llm.invoke("Explain quantum computing in detail.")
    print(f"Response: {result.content[:100]}...")

    # Check budget
    print("\n💰 Budget Status:")
    status = budget.get_status("production-budget")
    print(status)


def optimization_workflow():
    """Use tracking data to optimize model selection."""
    print("\n" + "=" * 60)
    print("MODEL OPTIMIZATION WORKFLOW")
    print("=" * 60)

    from token_calculator import ModelSelector

    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="langchain_costs.db")
    )

    # Current setup: using GPT-4 for everything
    current_callback = TokenCalculatorCallback(
        tracker=tracker,
        agent_id="current-agent",
        model_version="gpt-4"
    )

    llm_current = ChatOpenAI(
        model="gpt-4",
        callbacks=[current_callback]
    )

    # Run some queries
    print("\n📝 Running queries with GPT-4...")
    for query in [
        "What is 2+2?",
        "Explain machine learning",
        "Write a haiku about AI"
    ]:
        llm_current.invoke(query)

    # Get recommendation
    selector = ModelSelector(storage=tracker.storage)

    print("\n🎯 Getting model recommendation...")
    rec = selector.recommend(
        current_model="gpt-4",
        requirements={"max_cost_per_1k": 0.01},
        usage_context="simple_qa"
    )

    print(rec)

    if rec.monthly_savings > 10:
        print(f"\n💡 Recommendation: Switch to {rec.suggested_model}")
        print(f"   Expected savings: ${rec.monthly_savings:.2f}/month")

        # Test with recommended model
        print(f"\n🧪 Testing {rec.suggested_model}...")

        test_callback = TokenCalculatorCallback(
            tracker=tracker,
            agent_id="test-agent",
            model_version=rec.suggested_model
        )

        llm_test = ChatOpenAI(
            model=rec.suggested_model,
            callbacks=[test_callback]
        )

        test_result = llm_test.invoke("What is 2+2?")
        print(f"Result: {test_result.content}")

        # Compare costs
        print("\n💰 Cost Comparison:")
        comparison = tracker.get_costs(
            start_date="today",
            group_by=["model_version"]
        )
        print(comparison)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LANGCHAIN INTEGRATION EXAMPLES")
    print("Token Calculator + LangChain")
    print("=" * 60)

    # Run examples
    basic_integration()
    chain_integration()
    multi_agent_rag_system()
    production_monitoring()
    optimization_workflow()

    print("\n" + "=" * 60)
    print("✅ EXAMPLES COMPLETE")
    print("=" * 60)
    print("\n💡 Key Takeaways:")
    print("   • Add tracking with just callbacks=[callback]")
    print("   • Track multi-agent systems with different callbacks")
    print("   • Monitor production with budgets and alerts")
    print("   • Optimize with model recommendations")
