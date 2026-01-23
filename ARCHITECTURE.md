# Architecture Design: Token Calculator Enhancement

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  LangChain   │  │   CrewAI     │  │   Custom     │         │
│  │  Integration │  │  Integration │  │   App Code   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                  Token Calculator Core API                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Tracking & Monitoring Layer                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ CostTracker  │  │WorkflowTracker│ │ConvMonitor │  │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  │    │
│  └─────────┼──────────────────┼──────────────────┼─────────┘    │
│            │                  │                  │              │
│  ┌─────────┴──────────────────┴──────────────────┴─────────┐   │
│  │              Intelligence Layer                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │   │
│  │  │ Forecaster   │  │ModelSelector │  │HealthCheck │   │   │
│  │  └──────────────┘  └──────────────┘  └─────────────┘   │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │              Alert & Notification Layer                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐    │  │
│  │  │AlertManager  │  │BudgetTracker │  │ Notifier    │    │  │
│  │  └──────────────┘  └──────────────┘  └─────────────┘    │  │
│  └──────────────────────────┬───────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    Storage Abstraction Layer                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  StorageBackend (Abstract Interface)                     │  │
│  │  - save_event()                                          │  │
│  │  - query_events()                                        │  │
│  │  - aggregate()                                           │  │
│  └────┬───────────────┬───────────────┬──────────────┬──────┘  │
│       │               │               │              │          │
│  ┌────▼──────┐  ┌────▼──────┐  ┌────▼──────┐  ┌───▼──────┐   │
│  │ InMemory  │  │  SQLite   │  │PostgreSQL │  │  Custom  │   │
│  │  Backend  │  │  Backend  │  │  Backend  │  │  Backend │   │
│  └───────────┘  └───────────┘  └───────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Storage Layer

**File**: `token_calculator/storage.py`

**Purpose**: Provide pluggable storage backends for persistent tracking

**Classes**:

```python
class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def save_event(self, event: TrackingEvent) -> None:
        """Save a single tracking event"""

    @abstractmethod
    def query_events(self, filters: Dict, start_time: datetime,
                    end_time: datetime) -> List[TrackingEvent]:
        """Query events with filters"""

    @abstractmethod
    def aggregate(self, metric: str, group_by: List[str],
                 filters: Dict) -> Dict:
        """Aggregate metrics by dimensions"""

class InMemoryStorage(StorageBackend):
    """In-memory storage for development/testing"""

class SQLiteStorage(StorageBackend):
    """SQLite storage for single-machine production"""

class PostgreSQLStorage(StorageBackend):
    """PostgreSQL storage for distributed production"""
```

**Data Model**:

```python
@dataclass
class TrackingEvent:
    """Single tracking event"""
    event_id: str
    timestamp: datetime
    event_type: str  # "llm_call", "workflow_start", "workflow_end"
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    labels: Dict[str, str]  # Custom labels (agent_id, user_id, etc.)
    metadata: Dict[str, Any]  # Additional metadata
    parent_id: Optional[str]  # For workflow hierarchies
```

### 2. Cost Tracking

**File**: `token_calculator/cost_tracker.py`

**Purpose**: Track and analyze costs over time with custom dimensions

**Classes**:

```python
class CostTracker:
    """Track LLM costs over time with custom labels"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    def track_call(self, model: str, input_tokens: int,
                   output_tokens: int, **labels) -> CostRecord:
        """Track a single LLM call with custom labels"""

    def get_costs(self, start_date: str, end_date: str,
                 group_by: List[str], filters: Dict) -> CostReport:
        """Query costs with grouping and filtering"""

    def detect_anomalies(self, threshold: float = 2.0) -> List[Anomaly]:
        """Detect cost anomalies (>threshold * baseline)"""

    def get_recommendations(self, top_k: int = 5) -> List[Recommendation]:
        """Get top optimization recommendations"""
```

**Usage**:

```python
tracker = CostTracker(storage=SQLiteStorage("costs.db"))

# Track a call
tracker.track_call(
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    agent_id="customer-support",
    user_id="user-123",
    environment="production"
)

# Query costs
costs = tracker.get_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by=["agent_id", "model"],
    filters={"environment": "production"}
)
```

### 3. Multi-Agent Workflow Tracking

**File**: `token_calculator/workflow_tracker.py`

**Purpose**: Track token usage across multi-agent workflows

**Classes**:

```python
class WorkflowTracker:
    """Track multi-agent workflows"""

    def __init__(self, workflow_id: str, storage: StorageBackend):
        self.workflow_id = workflow_id
        self.storage = storage

    @contextmanager
    def track_agent(self, agent_id: str, **labels):
        """Context manager to track an agent's execution"""

    def analyze(self) -> WorkflowAnalysis:
        """Analyze workflow token usage and costs"""

    def suggest_optimizations(self) -> List[Optimization]:
        """Suggest workflow optimizations"""

    def visualize(self) -> str:
        """Generate ASCII visualization of workflow"""
```

**Usage**:

```python
tracker = WorkflowTracker(workflow_id="customer-support-v2")

with tracker.track_agent("planner"):
    planner_response = planner.run(query)

with tracker.track_agent("executor-1"):
    result1 = executor1.run(task1)

analysis = tracker.analyze()
print(f"Total cost: ${analysis.total_cost}")
print(f"Bottleneck: {analysis.bottleneck_agent}")
```

### 4. Context Health Monitoring

**File**: `token_calculator/health_monitor.py`

**Purpose**: Monitor context health and detect rot/degradation

**Classes**:

```python
class ConversationMonitor:
    """Monitor conversation context health"""

    def __init__(self, model: str, agent_id: str):
        self.model = model
        self.agent_id = agent_id
        self.context_analyzer = ContextAnalyzer(model)

    def add_turn(self, user_msg: str, assistant_msg: str):
        """Add a conversation turn"""

    def check_health(self) -> HealthStatus:
        """Check context health"""

    def compress_context(self, strategy: str,
                        target_tokens: int) -> List[Message]:
        """Compress context intelligently"""

@dataclass
class HealthStatus:
    """Context health status"""
    status: str  # "healthy", "context_rot", "hallucination_risk"
    context_usage: float  # 0-100%
    rot_percentage: float  # % of context that's irrelevant
    warnings: List[str]
    recommendations: List[str]
```

**Health Scoring Logic**:

```python
def calculate_health_score(conversation) -> HealthStatus:
    """
    Health score based on:
    1. Context utilization (>90% = risky)
    2. Message relevance (semantic similarity to recent context)
    3. Repetition (agent repeating itself = confusion)
    4. Topic coherence (sudden topic changes = prompt injection)
    """
```

### 5. Cost Forecasting & Budgeting

**File**: `token_calculator/forecasting.py`

**Purpose**: Forecast costs and track budgets

**Classes**:

```python
class CostForecaster:
    """Forecast costs based on historical data"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    def forecast_monthly(self, agent_id: str = None) -> Forecast:
        """Forecast next month's costs"""

    def scenario_model(self, scenario: Scenario) -> ScenarioResult:
        """Model a what-if scenario"""

class BudgetTracker:
    """Track budgets and spending"""

    def set_budget(self, amount: float, period: str,
                  filters: Dict = None):
        """Set a budget (monthly, weekly, daily)"""

    def get_remaining(self) -> BudgetStatus:
        """Get remaining budget"""

    def check_overage(self) -> bool:
        """Check if over budget"""
```

### 6. Alerting System

**File**: `token_calculator/alerts.py`

**Purpose**: Configure and send alerts

**Classes**:

```python
class AlertManager:
    """Manage alerts and notifications"""

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""

    def check_alerts(self, event: TrackingEvent) -> List[Alert]:
        """Check if event triggers any alerts"""

    def send_notification(self, alert: Alert):
        """Send notification (console, webhook, email)"""

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: Callable[[TrackingEvent], bool]
    severity: str  # "info", "warning", "critical"
    channels: List[str]  # "console", "webhook", "email"
    cooldown: int  # Seconds between alerts
```

**Usage**:

```python
alerts = AlertManager()

# Add budget alert
alerts.add_alert_rule(AlertRule(
    name="monthly-budget-80pct",
    condition=lambda e: budget_tracker.get_remaining().pct < 0.2,
    severity="warning",
    channels=["console", "webhook"]
))

# Add cost spike alert
alerts.add_alert_rule(AlertRule(
    name="cost-spike",
    condition=lambda e: e.cost > baseline * 2.0,
    severity="critical",
    channels=["console", "webhook", "email"]
))
```

### 7. Model Recommendation Engine

**File**: `token_calculator/model_selector.py`

**Purpose**: Recommend optimal models based on usage patterns

**Classes**:

```python
class ModelSelector:
    """Recommend optimal models"""

    def recommend(self, conversation_history: List[Message],
                 requirements: Dict) -> Recommendation:
        """Recommend best model for use case"""

    def create_ab_test(self, model_a: str, model_b: str,
                      duration_days: int) -> ABTest:
        """Create A/B test comparing models"""

@dataclass
class Recommendation:
    """Model recommendation"""
    suggested_model: str
    current_model: str
    monthly_savings: float
    quality_delta: float  # Expected quality impact (%)
    confidence: float  # 0-1
    reasoning: str
```

### 8. LangChain Integration

**File**: `token_calculator/integrations/langchain.py`

**Purpose**: One-line integration with LangChain

**Classes**:

```python
class TokenCalculatorCallback(BaseCallbackHandler):
    """LangChain callback for automatic tracking"""

    def __init__(self, tracker: CostTracker, **default_labels):
        self.tracker = tracker
        self.default_labels = default_labels

    def on_llm_start(self, ...):
        """Track LLM call start"""

    def on_llm_end(self, ...):
        """Track LLM call end with tokens and cost"""
```

**Usage**:

```python
from token_calculator.integrations.langchain import TokenCalculatorCallback

tracker = CostTracker(storage=SQLiteStorage("costs.db"))
callback = TokenCalculatorCallback(
    tracker=tracker,
    agent_id="rag-agent",
    environment="production"
)

llm = ChatOpenAI(callbacks=[callback])
# All LLM calls automatically tracked!
```

## Data Flow

### LLM Call Tracking Flow

```
1. Application calls LLM
   ↓
2. CostTracker.track_call() or Callback intercepts
   ↓
3. Calculate tokens (using TokenCounter)
   ↓
4. Calculate cost (using CostCalculator)
   ↓
5. Create TrackingEvent with labels/metadata
   ↓
6. Save to StorageBackend
   ↓
7. AlertManager.check_alerts()
   ↓
8. Send notifications if rules triggered
```

### Query Flow

```
1. User queries costs: tracker.get_costs(...)
   ↓
2. CostTracker builds query filters
   ↓
3. StorageBackend.query_events(filters)
   ↓
4. StorageBackend.aggregate(group_by)
   ↓
5. Return aggregated CostReport
```

### Workflow Tracking Flow

```
1. Start workflow: tracker = WorkflowTracker(workflow_id)
   ↓
2. Enter agent context: with tracker.track_agent("agent-1")
   ↓
3. Agent calls LLM (tracked with parent_id=workflow_id)
   ↓
4. Exit agent context (log agent completion)
   ↓
5. Analyze: tracker.analyze()
   ↓
6. Build workflow graph from parent_id relationships
   ↓
7. Calculate per-agent costs, identify bottlenecks
```

## Database Schema (SQLite/PostgreSQL)

### events table

```sql
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost REAL NOT NULL,
    parent_id TEXT,
    labels TEXT,  -- JSON blob
    metadata TEXT,  -- JSON blob
    INDEX idx_timestamp (timestamp),
    INDEX idx_event_type (event_type),
    INDEX idx_parent_id (parent_id)
);
```

### Query Optimization

```sql
-- For cost queries by agent and time
CREATE INDEX idx_labels_time ON events(
    json_extract(labels, '$.agent_id'),
    timestamp
);

-- For cost aggregation
CREATE INDEX idx_model_time ON events(model, timestamp);
```

## Configuration

### Environment Variables

```bash
# Storage backend
TOKEN_CALC_STORAGE=sqlite  # sqlite, postgresql, memory
TOKEN_CALC_STORAGE_PATH=/path/to/costs.db

# PostgreSQL (if used)
TOKEN_CALC_PG_HOST=localhost
TOKEN_CALC_PG_PORT=5432
TOKEN_CALC_PG_DATABASE=token_calculator
TOKEN_CALC_PG_USER=user
TOKEN_CALC_PG_PASSWORD=password

# Alerts
TOKEN_CALC_WEBHOOK_URL=https://hooks.slack.com/...
TOKEN_CALC_EMAIL_ALERTS=admin@company.com

# Default labels
TOKEN_CALC_DEFAULT_LABELS=environment:production,team:ai
```

### Configuration File

```python
# token_calculator.yaml
storage:
  backend: sqlite
  path: ./costs.db
  retention_days: 90

tracking:
  default_labels:
    environment: production
    team: ai-platform

alerts:
  rules:
    - name: monthly-budget-exceeded
      type: budget
      threshold: 1.0
      severity: critical
      channels: [webhook, email]

    - name: cost-spike
      type: anomaly
      threshold: 2.0
      severity: warning
      channels: [webhook]

budgets:
  - name: monthly-prod
    amount: 10000
    period: monthly
    filters:
      environment: production
```

## Migration Path

### From Current Version

```python
# Old way (still works)
from token_calculator import count_tokens, calculate_cost

tokens = count_tokens("prompt", "gpt-4")
cost = calculate_cost("gpt-4", tokens, 500)

# New way (enhanced)
from token_calculator import CostTracker, SQLiteStorage

tracker = CostTracker(storage=SQLiteStorage("costs.db"))
tracker.track_call(
    model="gpt-4",
    input_tokens=tokens,
    output_tokens=500,
    agent_id="my-agent"
)

# Query later
monthly_costs = tracker.get_costs(
    start_date="this-month",
    group_by=["agent_id"]
)
```

## Testing Strategy

### Unit Tests

```python
# Test storage backends
def test_sqlite_storage():
    storage = SQLiteStorage(":memory:")
    event = TrackingEvent(...)
    storage.save_event(event)
    results = storage.query_events(filters={})
    assert len(results) == 1

# Test cost tracking
def test_cost_tracker():
    tracker = CostTracker(InMemoryStorage())
    tracker.track_call("gpt-4", 1000, 500)
    costs = tracker.get_costs(group_by=["model"])
    assert costs.total_cost > 0
```

### Integration Tests

```python
# Test workflow tracking
def test_multi_agent_workflow():
    tracker = WorkflowTracker("test-workflow")
    with tracker.track_agent("agent-1"):
        # Simulate LLM call
        pass
    analysis = tracker.analyze()
    assert analysis.total_cost > 0
    assert len(analysis.agents) == 1
```

## Performance Targets

- **Tracking overhead**: <5ms per LLM call
- **Query latency**: <100ms for typical queries (1M events)
- **Storage efficiency**: ~200 bytes per event
- **Memory usage**: <50MB for in-memory storage (10K events)
- **Throughput**: >1000 events/sec

## Security Considerations

1. **PII Protection**: Don't log full prompts by default (opt-in)
2. **SQL Injection**: Use parameterized queries
3. **Access Control**: Storage backend handles authentication
4. **Encryption**: Support encrypted storage backends
5. **Audit Logs**: Track who accessed what data

## Backward Compatibility

All existing APIs remain unchanged. New features are additive:

```python
# All existing code works
from token_calculator import count_tokens, analyze_prompt
tokens = count_tokens("text", "gpt-4")  # Still works

# New features opt-in
from token_calculator import CostTracker
tracker = CostTracker()  # New capability
```
