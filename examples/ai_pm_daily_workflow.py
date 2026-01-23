"""
AI Product Manager Daily Workflow Example

This example shows how an AI PM building multi-agent systems uses
Token Calculator for daily cost monitoring, optimization, and troubleshooting.

Scenario: Managing a customer support agent system with:
- Classifier agent (routes requests)
- QA agent (simple questions)
- Complex agent (complex issues)
- Summarizer agent (conversation summaries)
"""

from token_calculator import (
    CostTracker,
    WorkflowTracker,
    ConversationMonitor,
    CostForecaster,
    BudgetTracker,
    AlertManager,
    ModelSelector,
    create_storage,
    AlertRule,
)


def morning_cost_review():
    """Morning routine: Check yesterday's costs and identify issues."""
    print("=" * 60)
    print("MORNING COST REVIEW")
    print("=" * 60)

    # Setup tracker with persistent storage
    storage = create_storage("sqlite", db_path="production_costs.db")
    tracker = CostTracker(
        storage=storage,
        default_labels={"environment": "production", "team": "ai-platform"}
    )

    # 1. Get yesterday's costs by agent
    print("\n📊 Yesterday's Costs by Agent:")
    yesterday_costs = tracker.get_costs(
        start_date="yesterday",
        group_by=["agent_id", "model"],
        filters={"environment": "production"}
    )
    print(yesterday_costs)

    # 2. Detect cost anomalies
    print("\n🔍 Cost Anomaly Detection:")
    anomalies = tracker.detect_anomalies(
        dimension="agent_id",
        threshold=2.0,  # Alert if 2x normal
        lookback_days=7
    )

    if anomalies:
        for anomaly in anomalies:
            print(f"\n{anomaly}")
    else:
        print("✅ No anomalies detected")

    # 3. Get optimization recommendations
    print("\n💡 Top Cost Optimization Opportunities:")
    recommendations = tracker.get_recommendations(top_k=5)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")

    return tracker


def check_budgets(tracker):
    """Check budget status and forecast for the month."""
    print("\n" + "=" * 60)
    print("BUDGET TRACKING")
    print("=" * 60)

    # Setup budget tracker
    budget_tracker = BudgetTracker(storage=tracker.storage)

    # Set monthly budget
    budget_tracker.set_budget(
        amount=10000,  # $10k/month
        period="monthly",
        filters={"environment": "production"},
        name="production-monthly"
    )

    # Check status
    status = budget_tracker.get_status("production-monthly")
    print(f"\n{status}")

    # Forecast rest of month
    forecaster = CostForecaster(storage=tracker.storage)
    forecast = forecaster.forecast_monthly()
    print(f"\n{forecast}")

    # Scenario: What if we get 2x more users?
    from token_calculator.forecasting import Scenario

    growth_scenario = Scenario(
        name="2x User Growth",
        description="Model doubling our user base",
        multipliers={"traffic": 2.0},
        expected_usage={}
    )

    scenario_result = forecaster.scenario_model(growth_scenario)
    print(f"\n{scenario_result}")


def track_multi_agent_workflow():
    """Track a multi-agent workflow execution."""
    print("\n" + "=" * 60)
    print("MULTI-AGENT WORKFLOW TRACKING")
    print("=" * 60)

    # Setup workflow tracker
    tracker = WorkflowTracker(
        workflow_id="customer-support-session-123",
        storage=create_storage("sqlite", db_path="production_costs.db"),
        environment="production",
        customer_id="cust_abc123"
    )

    # Simulate classifier agent
    print("\n🤖 Running classifier agent...")
    with tracker.track_agent("classifier", model="gpt-4o-mini") as ctx:
        # Simulate LLM call
        ctx.track_call(
            input_tokens=150,  # User query + system prompt
            output_tokens=20,  # Classification result
        )

    # Simulate QA agent (simple question)
    print("🤖 Running QA agent...")
    with tracker.track_agent("qa-agent", model="gpt-4o-mini") as ctx:
        # Simulate RAG retrieval + answer
        ctx.track_call(
            input_tokens=800,  # Context + RAG docs
            output_tokens=200,  # Answer
        )

    # Simulate summarizer
    print("🤖 Running summarizer agent...")
    with tracker.track_agent("summarizer", model="gpt-4o") as ctx:
        ctx.track_call(
            input_tokens=1000,  # Full conversation
            output_tokens=150,  # Summary
        )

    # Analyze workflow
    print("\n📈 Workflow Analysis:")
    analysis = tracker.analyze()
    print(analysis)

    # Get optimization suggestions
    print("\n💡 Workflow Optimizations:")
    suggestions = tracker.suggest_optimizations()
    for suggestion in suggestions:
        print(f"\n{suggestion}")

    # Visualize workflow
    print("\n📊 Workflow Visualization:")
    print(tracker.visualize())


def monitor_conversation_health():
    """Monitor a long conversation for context issues."""
    print("\n" + "=" * 60)
    print("CONVERSATION HEALTH MONITORING")
    print("=" * 60)

    # Setup monitor
    monitor = ConversationMonitor(
        model="gpt-4",
        agent_id="complex-support-agent"
    )

    # Simulate a long conversation
    conversation_turns = [
        ("What's your refund policy?", "Our refund policy allows..."),
        ("How long does processing take?", "Processing typically takes..."),
        ("Can I get a refund for subscription?", "Yes, subscription refunds..."),
        ("What about enterprise plans?", "Enterprise plans have..."),
        ("Do you support SSO?", "Yes, we support SSO via..."),
        ("What authentication methods?", "We support OAuth, SAML..."),
        ("Can I integrate with Slack?", "Yes, our Slack integration..."),
        ("What about Microsoft Teams?", "Teams integration is..."),
        ("How do I set up webhooks?", "Webhook setup requires..."),
        ("What's the rate limit?", "Our API rate limits are..."),
    ]

    print("\n🔄 Processing 10-turn conversation...")
    for i, (user_msg, assistant_msg) in enumerate(conversation_turns, 1):
        monitor.add_turn(user_msg, assistant_msg)

        # Check health every few turns
        if i % 3 == 0:
            health = monitor.check_health()
            print(f"\nTurn {i} Health Check:")
            print(health)

    # Final health check
    print("\n🏁 Final Health Check:")
    final_health = monitor.check_health()
    print(final_health)

    # If health is degraded, compress context
    if final_health.status in ["context_rot", "hallucination_risk"]:
        print("\n⚙️  Compressing context...")
        compression = monitor.compress_context(
            strategy="semantic",
            target_tokens=4000,
            keep_recent=3
        )
        print(compression)


def setup_alerting():
    """Setup proactive alerting for production monitoring."""
    print("\n" + "=" * 60)
    print("ALERTING SETUP")
    print("=" * 60)

    alerts = AlertManager(
        webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    )

    # 1. Budget alert (80% threshold)
    print("\n📢 Setting up budget alert (80% threshold)...")
    alerts.add_rule(AlertRule(
        name="budget-80pct",
        condition=lambda e: False,  # Would check cumulative budget
        severity="warning",
        message_template="Monthly budget 80% consumed",
        channels=["console", "webhook"],
        cooldown_minutes=60
    ))

    # 2. High cost call alert
    print("📢 Setting up high cost call alert...")
    alerts.add_rule(AlertRule(
        name="expensive-call",
        condition=lambda e: e.cost > 1.0,
        severity="warning",
        message_template="High cost LLM call: ${cost:.2f} for {agent_id}",
        channels=["console"],
        cooldown_minutes=30
    ))

    # 3. Context overflow warning
    print("📢 Setting up context overflow alert...")
    alerts.add_context_overflow_alert("gpt-4")

    print("\n✅ Alerts configured successfully!")
    print("💡 Alerts will trigger automatically on matching events")


def model_selection_workflow():
    """Use model selector to find optimal models."""
    print("\n" + "=" * 60)
    print("MODEL SELECTION & A/B TESTING")
    print("=" * 60)

    selector = ModelSelector(
        storage=create_storage("sqlite", db_path="production_costs.db")
    )

    # Get recommendation for simple Q&A
    print("\n🎯 Finding best model for simple Q&A:")
    rec = selector.recommend(
        current_model="gpt-4",
        requirements={
            "max_cost_per_1k": 0.01,
            "min_context": 8000
        },
        usage_context="simple_qa"
    )
    print(rec)

    # Setup A/B test
    print("\n🧪 Setting up A/B test (GPT-4 vs GPT-4o):")
    test = selector.create_ab_test(
        name="gpt4-vs-gpt4o-qa",
        model_a="gpt-4",
        model_b="gpt-4o",
        traffic_split=0.1,  # 10% to GPT-4o
        duration_days=7
    )
    print(f"✅ Test '{test.name}' created")
    print(f"   Duration: {test.duration_days} days")
    print(f"   Traffic split: {test.traffic_split*100:.0f}% to {test.model_b}")
    print("\n💡 Run for 7 days, then call selector.get_test_results(test)")


def incident_investigation():
    """Investigate a cost spike incident."""
    print("\n" + "=" * 60)
    print("INCIDENT INVESTIGATION: Cost Spike")
    print("=" * 60)

    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="production_costs.db")
    )

    print("\n🚨 Incident: Cost spike detected at 2:00 PM")
    print("\n🔍 Step 1: Get costs during incident window")

    # Get costs in incident window
    incident_costs = tracker.get_costs(
        start_date="2024-01-20T14:00:00",
        end_date="2024-01-20T15:00:00",
        group_by=["agent_id", "user_id", "model"]
    )

    print(incident_costs)

    print("\n🔍 Step 2: Compare to baseline (same hour yesterday)")
    baseline_costs = tracker.get_costs(
        start_date="2024-01-19T14:00:00",
        end_date="2024-01-19T15:00:00",
        group_by=["agent_id"]
    )

    print(f"Baseline cost: ${baseline_costs.total_cost:.2f}")
    print(f"Incident cost: ${incident_costs.total_cost:.2f}")
    print(f"Increase: {(incident_costs.total_cost / baseline_costs.total_cost - 1) * 100:.0f}%")

    print("\n🔍 Step 3: Identify root cause")
    print("💡 Analysis suggests:")
    print("   • Agent 'complex-agent' had 5x normal volume")
    print("   • User 'user_xyz' made 100+ requests")
    print("   • Likely: Retry loop or bot traffic")

    print("\n✅ Action: Add rate limiting for user_xyz")


def weekly_executive_report():
    """Generate executive-friendly weekly report."""
    print("\n" + "=" * 60)
    print("WEEKLY EXECUTIVE REPORT")
    print("=" * 60)

    tracker = CostTracker(
        storage=create_storage("sqlite", db_path="production_costs.db")
    )

    # This week
    this_week = tracker.get_costs(
        start_date="this-week",
        group_by=["agent_id"]
    )

    print("\n📊 This Week Summary:")
    print(f"   Total Cost: ${this_week.total_cost:.2f}")
    print(f"   Total Calls: {this_week.total_calls:,}")
    print(f"   Avg Cost/Call: ${this_week.total_cost/this_week.total_calls:.4f}")

    # Forecast next week
    forecaster = CostForecaster(storage=tracker.storage)
    forecast = forecaster.forecast_monthly()

    print(f"\n📈 Projections:")
    print(f"   Next Month: ${forecast.predicted_cost:.2f}")
    print(f"   Trend: {forecast.trend}")

    # ROI metrics (example)
    print(f"\n💰 Business Metrics:")
    print(f"   Cost per Conversation: ${this_week.total_cost / (this_week.total_calls / 3):.2f}")
    print(f"   Conversations Handled: {this_week.total_calls // 3:,}")

    print(f"\n✅ Key Wins:")
    print(f"   • Reduced cost per call by 15% vs last month")
    print(f"   • Prevented 12 context overflow incidents")
    print(f"   • Optimized 3 agents, saving $500/mo")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI PRODUCT MANAGER - DAILY WORKFLOW DEMO")
    print("Token Calculator for Production AI Systems")
    print("=" * 60)

    # Morning routine
    tracker = morning_cost_review()

    # Budget check
    check_budgets(tracker)

    # Track workflow
    track_multi_agent_workflow()

    # Monitor conversation health
    monitor_conversation_health()

    # Setup alerts
    setup_alerting()

    # Model selection
    model_selection_workflow()

    # Incident investigation
    incident_investigation()

    # Weekly report
    weekly_executive_report()

    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Integrate with your LLM calls using CostTracker")
    print("   2. Set up alerting with AlertManager")
    print("   3. Monitor budgets with BudgetTracker")
    print("   4. Run weekly reports for stakeholders")
    print("\n📚 See docs for integration guides:")
    print("   • LangChain: examples/langchain_integration.py")
    print("   • Custom: examples/custom_integration.py")
