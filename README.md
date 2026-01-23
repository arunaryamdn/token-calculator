# 🎯 Token Calculator

[![PyPI version](https://badge.fury.io/py/token-calculator.svg)](https://badge.fury.io/py/token-calculator)
[![Downloads](https://pepy.tech/badge/token-calculator)](https://pepy.tech/project/token-calculator)

**Production-Ready LLM Cost Management and Observability for AI Product Managers**

Token Calculator is the comprehensive toolkit for building, monitoring, and optimizing production AI agents. Track costs across multi-agent workflows, detect context rot before it causes hallucinations, and make data-driven decisions about model selection—all with enterprise-grade observability.

## 🎯 Built for AI Product Managers

If you're building AI agents in production, you know the challenges:

- 💸 **Cost Blindness**: You don't see costs until the monthly bill arrives
- 🤖 **Multi-Agent Complexity**: Hard to track which agent in your workflow costs what
- 🔥 **Context Rot**: Conversations degrade over time, causing hallucinations
- 📊 **No Visibility**: Can't debug token usage through complex agent workflows
- 🎲 **Model Selection**: Guessing which model offers the best cost/quality trade-off
- ⚠️ **Production Incidents**: Context overflows break your app at 2 AM

**Token Calculator solves all of these problems.**

## ✨ Key Features for Production AI

### 📊 **Cost Tracking with Multi-Dimensional Analysis**

Track every LLM call with custom labels, query costs by any dimension, and identify cost anomalies before they become incidents.

```python
from token_calculator import CostTracker, create_storage

# Track with custom dimensions
tracker = CostTracker(
    storage=create_storage("sqlite", db_path="costs.db"),
    default_labels={"environment": "production", "team": "ai"}
)

tracker.track_call(
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    agent_id="customer-support",
    user_id="user-123",
    session_id="session-456"
)

# Query costs by any dimension
report = tracker.get_costs(
    start_date="this-month",
    group_by=["agent_id", "model"],
    filters={"environment": "production"}
)
print(report)
# Output:
# Cost Report (1,234 calls)
#   Total Cost: $456.78
#   Breakdown:
#     customer-support | gpt-4: $234.56
#     rag-agent | gpt-4o: $123.45
```

### 🤖 **Multi-Agent Workflow Tracking**

Track token usage across complex agent orchestrations, identify bottlenecks, and optimize inter-agent communication.

```python
from token_calculator import WorkflowTracker

tracker = WorkflowTracker(workflow_id="customer-support-v2")

# Track each agent in your workflow
with tracker.track_agent("router", model="gpt-4o-mini") as ctx:
    result = router.run(query)
    ctx.track_call(input_tokens=150, output_tokens=20)

with tracker.track_agent("executor", model="gpt-4") as ctx:
    final = executor.run(result)
    ctx.track_call(input_tokens=800, output_tokens=300)

# Analyze workflow
analysis = tracker.analyze()
print(analysis)
# Output:
# Workflow Analysis: customer-support-v2
#   Total Cost: $0.0520
#   Bottleneck: executor ($0.0450)
#   Efficiency: 75/100
#   Recommendations:
#     • executor accounts for >50% of cost
```

### 🏥 **Context Health Monitoring**

Detect context rot, prevent hallucinations, and intelligently compress conversations before quality degrades.

```python
from token_calculator import ConversationMonitor

monitor = ConversationMonitor(model="gpt-4", agent_id="support-agent")

for user_msg, assistant_msg in conversation:
    monitor.add_turn(user_msg, assistant_msg)

    health = monitor.check_health()

    if health.status == "context_rot":
        # Compress before quality degrades
        compressed = monitor.compress_context(
            strategy="semantic",
            target_tokens=4000,
            keep_recent=3
        )
        # Reset conversation with compressed context

print(health)
# Output:
# ⚠️ Context Health: CONTEXT_ROT
#   Quality Score: 65/100
#   Context Usage: 78.5%
#   Rot: 45.0%
#   Warnings:
#     ⚠️  45% of context appears irrelevant
#   Recommendations:
#     💡 Use compress_context() to remove irrelevant context
```

### 📈 **Cost Forecasting & Budgeting**

Forecast future costs, set budgets, and get alerted before you overspend.

```python
from token_calculator import CostForecaster, BudgetTracker

forecaster = CostForecaster(storage=tracker.storage)

# Forecast next month
forecast = forecaster.forecast_monthly(agent_id="rag-agent")
print(forecast)
# Output:
# 📈 Monthly Forecast:
#   Predicted: $1,234.56
#   Range: $987.65 - $1,481.47
#   Trend: increasing

# Set budget and track
budget = BudgetTracker(storage=tracker.storage)
budget.set_budget(amount=10000, period="monthly")

status = budget.get_status()
if not status.on_track:
    print(f"⚠️ Projected overage: ${status.projected_overage:.2f}")
```

### 🚨 **Real-Time Alerting**

Get notified immediately when costs spike, contexts overflow, or budgets are exceeded.

```python
from token_calculator import AlertManager, AlertRule

alerts = AlertManager(webhook_url="https://hooks.slack.com/...")

# Cost spike alert
alerts.add_rule(AlertRule(
    name="cost-spike",
    condition=lambda e: e.cost > 1.0,
    severity="warning",
    message_template="High cost call: ${cost:.2f} for {agent_id}",
    channels=["console", "webhook"]
))

# Budget alert
alerts.add_budget_alert(
    budget_amount=10000,
    threshold_pct=0.8,  # Alert at 80%
    severity="warning"
)

# Alerts trigger automatically
triggered = alerts.check_event(event)
```

### 🎯 **Model Recommendation Engine**

Stop guessing which model to use. Get data-driven recommendations based on your usage patterns.

```python
from token_calculator import ModelSelector

selector = ModelSelector(storage=tracker.storage)

# Get recommendation
rec = selector.recommend(
    current_model="gpt-4",
    requirements={"max_cost_per_1k": 0.01},
    usage_context="simple_qa"
)

print(rec)
# Output:
# 💡 Model Recommendation: gpt-4o-mini
#    Current: gpt-4
#    Monthly Savings: $450.00
#    Quality Impact: -10%
#    Confidence: 85%
#    Reasoning: gpt-4o-mini costs <50% of gpt-4. Fast, cost-effective for simple Q&A

# A/B test the recommendation
test = selector.create_ab_test(
    name="gpt4-vs-gpt4o",
    model_a="gpt-4",
    model_b="gpt-4o",
    traffic_split=0.1,
    duration_days=7
)

# After 7 days...
results = selector.get_test_results(test)
print(results.recommendation)
```

### 🔌 **One-Line LangChain Integration**

Already using LangChain? Add tracking with one line of code.

```python
from langchain_openai import ChatOpenAI
from token_calculator import CostTracker, create_storage
from token_calculator.integrations.langchain import TokenCalculatorCallback

tracker = CostTracker(storage=create_storage("sqlite", db_path="costs.db"))

callback = TokenCalculatorCallback(
    tracker=tracker,
    agent_id="my-agent",
    environment="production"
)

# Just add callbacks parameter!
llm = ChatOpenAI(callbacks=[callback])

# All LLM calls are now tracked automatically
result = llm.invoke("Hello!")

# Check costs
report = tracker.get_costs(start_date="today")
```

## 📦 Installation

```bash
pip install token-calculator
```

Optional dependencies:

```bash
# For LangChain integration
pip install token-calculator[langchain]

# For PostgreSQL storage
pip install token-calculator[postgres]

# All optional dependencies
pip install token-calculator[all]
```

## 🚀 Quick Start

### 1. Basic Cost Tracking

```python
from token_calculator import CostTracker, create_storage

tracker = CostTracker(
    storage=create_storage("sqlite", db_path="costs.db")
)

# Track LLM calls
tracker.track_call(
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    agent_id="my-agent"
)

# Get costs
report = tracker.get_costs(start_date="this-month")
print(f"Total cost: ${report.total_cost:.2f}")
```

### 2. Multi-Agent Workflow

```python
from token_calculator import WorkflowTracker

tracker = WorkflowTracker(workflow_id="my-workflow")

with tracker.track_agent("planner", model="gpt-4o") as ctx:
    # Your agent code
    ctx.track_call(input_tokens=500, output_tokens=100)

with tracker.track_agent("executor", model="gpt-4") as ctx:
    # Your agent code
    ctx.track_call(input_tokens=1000, output_tokens=300)

analysis = tracker.analyze()
print(f"Total cost: ${analysis.total_cost:.4f}")
```

### 3. Context Health Monitoring

```python
from token_calculator import ConversationMonitor

monitor = ConversationMonitor(model="gpt-4")

monitor.add_turn(
    user_message="What's the weather?",
    assistant_message="I don't have real-time weather data."
)

health = monitor.check_health()
if health.status != "healthy":
    print(health.recommendations)
```

## 📚 Complete Examples

### AI Product Manager Daily Workflow

See [`examples/ai_pm_daily_workflow.py`](examples/ai_pm_daily_workflow.py) for a complete example showing:

- ✅ Morning cost review and anomaly detection
- ✅ Budget tracking and forecasting
- ✅ Multi-agent workflow tracking
- ✅ Context health monitoring
- ✅ Setting up alerts
- ✅ Model selection and A/B testing
- ✅ Incident investigation
- ✅ Weekly executive reporting

### LangChain Integration

See [`examples/langchain_integration.py`](examples/langchain_integration.py) for:

- ✅ Basic LangChain integration
- ✅ Chain tracking
- ✅ Multi-agent RAG systems
- ✅ Production monitoring
- ✅ Model optimization

## 🏗️ Architecture

Token Calculator uses a modular architecture:

```
Application Layer (Your Code)
    ↓
Tracking Layer (CostTracker, WorkflowTracker, ConversationMonitor)
    ↓
Intelligence Layer (Forecaster, ModelSelector, HealthCheck)
    ↓
Alert Layer (AlertManager, BudgetTracker)
    ↓
Storage Layer (SQLite, PostgreSQL, In-Memory)
```

### Storage Backends

- **In-Memory**: Fast, for testing/development
- **SQLite**: Production-ready for single-machine deployments
- **PostgreSQL**: Multi-instance production deployments

```python
# SQLite
storage = create_storage("sqlite", db_path="costs.db")

# PostgreSQL
storage = create_storage(
    "postgresql",
    host="localhost",
    database="token_calculator",
    user="user",
    password="pass"
)

# In-Memory
storage = create_storage("memory")
```

## 📊 Supported Models

**40+ models** across 6 providers:

- ✅ **OpenAI**: GPT-4, GPT-4 Turbo, GPT-4o, GPT-4o-mini, GPT-3.5 Turbo
- ✅ **Anthropic**: Claude 4.5 Opus, Claude 3.5 Sonnet, Claude 3.5 Haiku
- ✅ **Google**: Gemini Pro, Gemini 1.5 Pro, Gemini 1.5 Flash
- ✅ **Meta**: Llama 2, Llama 3, Llama 3.1 (all sizes)
- ✅ **Mistral**: Mistral 7B, 8x7B, Small, Medium, Large
- ✅ **Cohere**: Command, Command R, Command R+

## 🎯 Use Cases

### For AI Product Managers

- 📊 Track costs across all agents and workflows
- 🎯 Identify which agents/users drive costs
- 📈 Forecast costs and plan budgets
- 🚨 Get alerted before incidents
- 💡 Optimize model selection for cost/quality
- 📋 Generate executive reports

### For AI Engineers

- 🔍 Debug token usage in complex workflows
- 🏥 Monitor context health and prevent degradation
- ⚡ Optimize prompts systematically
- 🧪 A/B test different models
- 🔌 Integrate with existing LangChain apps

### For AI Teams

- 💰 Shared budget tracking
- 📊 Cross-team cost visibility
- 🎯 Standardized monitoring
- 🚨 Centralized alerting
- 📈 Trend analysis

## 🔧 Configuration

### Environment Variables

```bash
# Storage
export TOKEN_CALC_STORAGE=sqlite
export TOKEN_CALC_STORAGE_PATH=/path/to/costs.db

# Alerts
export TOKEN_CALC_WEBHOOK_URL=https://hooks.slack.com/...

# Default labels
export TOKEN_CALC_DEFAULT_LABELS=environment:production,team:ai
```

### Configuration File

```yaml
# token_calculator.yaml
storage:
  backend: sqlite
  path: ./costs.db

tracking:
  default_labels:
    environment: production
    team: ai-platform

alerts:
  rules:
    - name: budget-exceeded
      type: budget
      threshold: 1.0
      severity: critical

budgets:
  - name: monthly-prod
    amount: 10000
    period: monthly
```

## 📖 Documentation

- [Product Requirements Document](PRD.md) - Vision and requirements
- [Architecture Design](ARCHITECTURE.md) - Technical architecture
- [Gap Analysis](GAP_ANALYSIS.md) - Feature roadmap

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built for AI Product Managers building the future of AI agents.

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/arunaryamdn/token-calculator/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/arunaryamdn/token-calculator/discussions)
- 📧 **Email**: [Contact](mailto:support@tokencalculator.com)

---

**Built with ❤️ for AI Product Managers**

Stop guessing. Start measuring. Build better AI agents.
