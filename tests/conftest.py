"""pytest configuration and fixtures for token-calculator tests."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pytest

from token_calculator import (
    AlertManager,
    BudgetTracker,
    ConversationMonitor,
    CostForecaster,
    CostTracker,
    InMemoryStorage,
    ModelSelector,
    SQLiteStorage,
    TrackingEvent,
    WorkflowTracker,
)

# ============================================================================
# Storage Backend Fixtures
# ============================================================================


@pytest.fixture
def temp_db_path():
    """Temporary SQLite database file."""
    import time

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup - retry on Windows file locking issues
    for _ in range(5):
        try:
            Path(db_path).unlink(missing_ok=True)
            break
        except PermissionError:
            time.sleep(0.1)  # Small delay to allow file to be released


@pytest.fixture
def memory_storage():
    """In-memory storage backend."""
    return InMemoryStorage()


@pytest.fixture
def sqlite_storage(temp_db_path):
    """SQLite storage backend with temporary database."""
    return SQLiteStorage(temp_db_path)


@pytest.fixture(params=["memory", "sqlite"])
def storage_backend(request, temp_db_path):
    """Parametrized storage backend fixture.

    Runs tests on both InMemoryStorage and SQLiteStorage to ensure
    consistency across backends.
    """
    if request.param == "memory":
        return InMemoryStorage()
    elif request.param == "sqlite":
        return SQLiteStorage(temp_db_path)


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_tracking_event():
    """Sample tracking event for LLM call."""
    return TrackingEvent.create_llm_call(
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500,
        cost=0.045,
        agent_id="test-agent",
        environment="test",
    )


@pytest.fixture
def sample_tracking_events():
    """List of sample tracking events with variety."""
    events = []

    # Different models
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]

    # Different agents
    agents = ["agent-1", "agent-2", "agent-3"]

    # Different environments
    environments = ["dev", "staging", "prod"]

    for i in range(20):
        event = TrackingEvent.create_llm_call(
            model=models[i % len(models)],
            input_tokens=100 + (i * 50),
            output_tokens=50 + (i * 25),
            cost=0.01 + (i * 0.005),
            agent_id=agents[i % len(agents)],
            environment=environments[i % len(environments)],
            metadata={"iteration": i},
        )
        events.append(event)

    return events


@pytest.fixture
def sample_messages():
    """Sample chat messages for token counting."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! How are you today?"},
        {
            "role": "assistant",
            "content": "I'm doing well, thank you! How can I help you?",
        },
        {"role": "user", "content": "Can you explain quantum physics?"},
    ]


@pytest.fixture
def sample_multimodal_messages():
    """Sample multimodal messages (text + images)."""
    return [
        {"role": "user", "content": "What's in this image?"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this image:"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"},
                },
            ],
        },
    ]


@pytest.fixture
def sample_conversation():
    """Sample conversation for context health monitoring."""
    from token_calculator.health_monitor import Message

    messages = [
        Message(role="system", content="You are a coding assistant.", tokens=10),
        Message(role="user", content="Write a function to sort a list.", tokens=12),
        Message(
            role="assistant",
            content="def sort_list(lst): return sorted(lst)",
            tokens=15,
        ),
        Message(role="user", content="Add error handling.", tokens=8),
        Message(
            role="assistant",
            content="def sort_list(lst):\n    try:\n        return sorted(lst)\n    except:\n        return []",
            tokens=25,
        ),
    ]

    return messages


# ============================================================================
# Tracker Fixtures
# ============================================================================


@pytest.fixture
def cost_tracker(memory_storage):
    """CostTracker with in-memory storage."""
    return CostTracker(memory_storage)


@pytest.fixture
def workflow_tracker(memory_storage):
    """WorkflowTracker with in-memory storage."""
    return WorkflowTracker(memory_storage)


@pytest.fixture
def budget_tracker(memory_storage):
    """BudgetTracker with in-memory storage."""
    return BudgetTracker(memory_storage)


@pytest.fixture
def cost_forecaster(memory_storage):
    """CostForecaster with in-memory storage."""
    return CostForecaster(memory_storage)


@pytest.fixture
def health_monitor():
    """ConversationMonitor instance."""
    return ConversationMonitor()


@pytest.fixture
def model_selector(memory_storage):
    """ModelSelector with in-memory storage."""
    return ModelSelector(memory_storage)


# ============================================================================
# Alert Manager Fixtures
# ============================================================================


@pytest.fixture
def alert_manager():
    """AlertManager without webhook."""
    return AlertManager()


@pytest.fixture
def alert_manager_with_webhook():
    """AlertManager with test webhook URL."""
    return AlertManager(webhook_url="https://hooks.example.com/test")


# ============================================================================
# Populated Storage Fixtures
# ============================================================================


@pytest.fixture
def populated_storage(memory_storage, sample_tracking_events):
    """Storage backend with sample events pre-populated."""
    for event in sample_tracking_events:
        memory_storage.save_event(event)
    return memory_storage


@pytest.fixture
def time_series_storage(memory_storage):
    """Storage with time-series events for forecasting tests."""
    base_time = datetime.now() - timedelta(days=30)

    for day in range(30):
        event_time = base_time + timedelta(days=day)

        # Create 3-5 events per day with varying costs
        for i in range(3 + (day % 3)):
            event = TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=500 + (day * 10),
                output_tokens=250 + (day * 5),
                cost=0.02 + (day * 0.001),
                agent_id="test-agent",
                environment="prod",
            )
            # Override timestamp to create time series
            event.timestamp = event_time + timedelta(hours=i * 2)
            memory_storage.save_event(event)

    return memory_storage


# ============================================================================
# Workflow Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow(workflow_tracker):
    """Sample workflow with multiple agents."""
    # Start workflow
    workflow_id = workflow_tracker.start_workflow(name="data-pipeline", description="Test workflow")

    # Track agents
    workflow_tracker.track_agent(
        workflow_id=workflow_id,
        agent_name="loader",
        model="gpt-3.5-turbo",
        input_tokens=200,
        output_tokens=100,
        cost=0.001,
    )

    workflow_tracker.track_agent(
        workflow_id=workflow_id,
        agent_name="processor",
        model="gpt-4",
        input_tokens=500,
        output_tokens=300,
        cost=0.025,
    )

    workflow_tracker.track_agent(
        workflow_id=workflow_id,
        agent_name="summarizer",
        model="claude-3-sonnet",
        input_tokens=300,
        output_tokens=150,
        cost=0.012,
    )

    return workflow_id


# ============================================================================
# Security Test Fixtures
# ============================================================================


@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection attack payloads."""
    return [
        "'; DROP TABLE events; --",
        "' OR '1'='1",
        '" OR "1"="1',
        "'; DELETE FROM events WHERE '1'='1",
        "' UNION SELECT * FROM users --",
        "../../../etc/passwd",
        "admin'--",
        "1' OR '1' = '1'/*",
    ]


@pytest.fixture
def ssrf_attack_urls():
    """Common SSRF attack URLs."""
    return [
        ("http://localhost/evil", "localhost"),
        ("https://127.0.0.1/hack", "127.0.0.1"),
        ("https://192.168.1.1/internal", "private IP 192.168.1.1"),
        ("https://10.0.0.1/internal", "private IP 10.0.0.1"),
        ("https://172.16.0.1/internal", "private IP 172.16.0.1"),
        ("https://169.254.169.254/meta-data", "metadata service"),
        ("http://0.0.0.0/evil", "0.0.0.0"),
        ("https://[::1]/local", "IPv6 localhost"),
    ]


# ============================================================================
# Model Test Fixtures
# ============================================================================


@pytest.fixture
def sample_model_requirements():
    """Sample requirements for model selection."""
    return {
        "max_cost_per_1k_tokens": 0.03,
        "min_context_window": 8000,
        "required_features": ["function_calling"],
    }


# ============================================================================
# Budget Fixtures
# ============================================================================


@pytest.fixture
def active_budget(budget_tracker):
    """Active budget for testing."""
    budget_tracker.set_budget(amount=1000.0, period="monthly", name="test-budget")
    return budget_tracker


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration between tests."""
    import logging

    yield

    # Reset logging to avoid interference between tests
    logger = logging.getLogger("token_calculator")
    logger.handlers.clear()
    logger.setLevel(logging.WARNING)
