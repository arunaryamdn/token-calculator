"""Comprehensive tests for storage backends.

Tests for:
- TrackingEvent data model
- InMemoryStorage operations
- SQLiteStorage operations
- Storage backend common behavior
- Storage factory function
"""

import json
from datetime import datetime, timedelta

import pytest

from token_calculator import (
    InMemoryStorage,
    SQLiteStorage,
    StorageBackend,
    StorageError,
    TrackingEvent,
    create_storage,
)

# ============================================================================
# TrackingEvent Tests
# ============================================================================


class TestTrackingEvent:
    """Test TrackingEvent data model."""

    def test_create_llm_call_basic(self):
        """Test creating basic LLM call event."""
        event = TrackingEvent.create_llm_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.015,
        )

        assert event.event_type == "llm_call"
        assert event.model == "gpt-4"
        assert event.input_tokens == 100
        assert event.output_tokens == 50
        assert event.cost == 0.015
        assert isinstance(event.timestamp, datetime)
        assert event.event_id is not None
        assert event.parent_id is None

    def test_create_llm_call_with_labels(self):
        """Test creating LLM call with custom labels."""
        event = TrackingEvent.create_llm_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.015,
            agent_id="my-agent",
            environment="production",
            user_id="user-123",
        )

        assert event.labels["agent_id"] == "my-agent"
        assert event.labels["environment"] == "production"
        assert event.labels["user_id"] == "user-123"

    def test_create_llm_call_with_metadata(self):
        """Test creating LLM call and adding metadata manually."""
        event = TrackingEvent.create_llm_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.015,
        )

        # Metadata can be added manually
        event.metadata = {"request_id": "req-123", "session_id": "sess-456"}

        assert event.metadata["request_id"] == "req-123"
        assert event.metadata["session_id"] == "sess-456"

    def test_create_llm_call_with_parent(self):
        """Test creating child event with parent_id."""
        parent = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
        )

        child = TrackingEvent.create_llm_call(
            model="gpt-3.5-turbo",
            input_tokens=50,
            output_tokens=25,
            cost=0.005,
        )

        # Set parent_id manually
        child.parent_id = parent.event_id

        assert child.parent_id == parent.event_id

    def test_event_id_is_unique(self):
        """Test that each event gets a unique ID."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
            )
            for _ in range(10)
        ]

        event_ids = [e.event_id for e in events]
        assert len(set(event_ids)) == 10  # All unique


# ============================================================================
# InMemoryStorage Tests
# ============================================================================


class TestInMemoryStorage:
    """Test InMemoryStorage backend."""

    def test_initialization(self):
        """Test storage initializes correctly."""
        storage = InMemoryStorage()
        assert isinstance(storage, StorageBackend)
        assert len(storage.events) == 0

    def test_save_single_event(self, memory_storage):
        """Test saving a single event."""
        event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
        )

        memory_storage.save_event(event)

        assert len(memory_storage.events) == 1
        assert memory_storage.events[0].event_id == event.event_id

    def test_save_multiple_events(self, memory_storage):
        """Test saving multiple events."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100 + i, output_tokens=50, cost=0.015
            )
            for i in range(5)
        ]

        for event in events:
            memory_storage.save_event(event)

        assert len(memory_storage.events) == 5

    def test_query_all_events(self, memory_storage):
        """Test querying all events."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
            )
            for _ in range(3)
        ]

        for event in events:
            memory_storage.save_event(event)

        results = memory_storage.query_events()
        assert len(results) == 3

    def test_query_with_time_filters(self, memory_storage):
        """Test querying with time range filters."""
        now = datetime.now()
        past = now - timedelta(hours=2)
        future = now + timedelta(hours=2)

        event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
        )
        memory_storage.save_event(event)

        # Query with time range that includes the event
        results = memory_storage.query_events(start_time=past, end_time=future)
        assert len(results) == 1

        # Query with time range that excludes the event
        results = memory_storage.query_events(
            start_time=future, end_time=future + timedelta(hours=1)
        )
        assert len(results) == 0

    def test_query_with_filters(self, memory_storage):
        """Test querying with label filters."""
        event1 = TrackingEvent.create_llm_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.015,
            agent_id="agent-1",
            environment="prod",
        )
        event2 = TrackingEvent.create_llm_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.015,
            agent_id="agent-2",
            environment="dev",
        )

        memory_storage.save_event(event1)
        memory_storage.save_event(event2)

        # Filter by agent_id
        results = memory_storage.query_events(filters={"agent_id": "agent-1"})
        assert len(results) == 1
        assert results[0].labels["agent_id"] == "agent-1"

        # Filter by environment
        results = memory_storage.query_events(filters={"environment": "dev"})
        assert len(results) == 1
        assert results[0].labels["environment"] == "dev"

    def test_query_with_limit_and_offset(self, memory_storage):
        """Test querying with pagination."""
        for i in range(10):
            event = TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.015,
                index=str(i),
            )
            memory_storage.save_event(event)

        # Get first 5
        results = memory_storage.query_events(limit=5, offset=0)
        assert len(results) == 5

        # Get next 5
        results = memory_storage.query_events(limit=5, offset=5)
        assert len(results) == 5

        # Get last 3
        results = memory_storage.query_events(limit=5, offset=7)
        assert len(results) == 3


# ============================================================================
# SQLiteStorage Tests
# ============================================================================


class TestSQLiteStorage:
    """Test SQLiteStorage backend."""

    def test_initialization_creates_db(self, temp_db_path):
        """Test storage creates database file."""
        storage = SQLiteStorage(temp_db_path)

        # Database file should exist
        from pathlib import Path

        assert Path(temp_db_path).exists()

    def test_initialization_creates_tables(self, sqlite_storage):
        """Test storage creates required tables."""
        # Try to save and retrieve an event
        event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
        )
        sqlite_storage.save_event(event)

        results = sqlite_storage.query_events()
        assert len(results) == 1

    def test_memory_database(self):
        """Test in-memory SQLite database."""
        storage = SQLiteStorage(":memory:")

        event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
        )
        storage.save_event(event)

        results = storage.query_events()
        assert len(results) == 1

    def test_event_persistence(self, temp_db_path):
        """Test events persist across storage instances."""
        # Create storage and save event
        storage1 = SQLiteStorage(temp_db_path)
        event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
        )
        storage1.save_event(event)

        # Create new storage instance and query
        storage2 = SQLiteStorage(temp_db_path)
        results = storage2.query_events()
        assert len(results) == 1
        assert results[0].event_id == event.event_id

    def test_json_serialization(self, sqlite_storage):
        """Test that labels and metadata are properly serialized."""
        event = TrackingEvent.create_llm_call(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            cost=0.015,
            agent_id="test-agent",
        )
        # Add metadata manually
        event.metadata = {"key": "value", "number": 42, "nested": {"a": 1}}

        sqlite_storage.save_event(event)

        results = sqlite_storage.query_events()
        assert len(results) == 1
        assert results[0].labels["agent_id"] == "test-agent"
        assert results[0].metadata["key"] == "value"
        assert results[0].metadata["number"] == 42
        assert results[0].metadata["nested"]["a"] == 1


# ============================================================================
# Common Backend Tests (Parametrized)
# ============================================================================


class TestStorageBackendCommon:
    """Test common behavior across all storage backends."""

    def test_aggregate_cost(self, storage_backend):
        """Test cost aggregation."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100, output_tokens=50, cost=0.01 + i * 0.01
            )
            for i in range(5)
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="cost")
        assert result["total"] == pytest.approx(0.01 + 0.02 + 0.03 + 0.04 + 0.05)

    def test_aggregate_input_tokens(self, storage_backend):
        """Test input tokens aggregation."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100 + i * 10, output_tokens=50, cost=0.015
            )
            for i in range(3)
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="input_tokens")
        assert result["total"] == 100 + 110 + 120

    def test_aggregate_output_tokens(self, storage_backend):
        """Test output tokens aggregation."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100, output_tokens=50 + i * 5, cost=0.015
            )
            for i in range(3)
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="output_tokens")
        assert result["total"] == 50 + 55 + 60

    def test_aggregate_count(self, storage_backend):
        """Test event count aggregation."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4", input_tokens=100, output_tokens=50, cost=0.015
            )
            for _ in range(7)
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="count")
        assert result["total"] == 7

    def test_aggregate_with_group_by(self, storage_backend):
        """Test aggregation with grouping."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.01,
                agent_id="agent-1",
            ),
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.02,
                agent_id="agent-1",
            ),
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.03,
                agent_id="agent-2",
            ),
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="cost", group_by=["agent_id"])

        assert ("agent-1",) in result
        assert ("agent-2",) in result
        assert result[("agent-1",)] == pytest.approx(0.03)
        assert result[("agent-2",)] == pytest.approx(0.03)

    def test_aggregate_with_multiple_dimensions(self, storage_backend):
        """Test aggregation with multiple grouping dimensions."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.01,
                agent_id="agent-1",
                environment="prod",
            ),
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.02,
                agent_id="agent-1",
                environment="dev",
            ),
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.03,
                agent_id="agent-2",
                environment="prod",
            ),
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="cost", group_by=["agent_id", "environment"])

        assert ("agent-1", "prod") in result
        assert ("agent-1", "dev") in result
        assert ("agent-2", "prod") in result
        assert result[("agent-1", "prod")] == pytest.approx(0.01)

    def test_aggregate_with_filters(self, storage_backend):
        """Test aggregation with filters."""
        events = [
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.01,
                agent_id="agent-1",
            ),
            TrackingEvent.create_llm_call(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                cost=0.02,
                agent_id="agent-2",
            ),
        ]

        for event in events:
            storage_backend.save_event(event)

        result = storage_backend.aggregate(metric="cost", filters={"agent_id": "agent-1"})

        assert result["total"] == pytest.approx(0.01)

    def test_aggregate_with_time_range(self, storage_backend):
        """Test aggregation with time range."""
        now = datetime.now()
        past = now - timedelta(hours=2)

        # Event in the past
        event1 = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.01
        )
        event1.timestamp = past
        storage_backend.save_event(event1)

        # Event now
        event2 = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.02
        )
        storage_backend.save_event(event2)

        # Aggregate only recent events
        result = storage_backend.aggregate(metric="cost", start_time=now - timedelta(hours=1))

        assert result["total"] == pytest.approx(0.02)

    def test_aggregate_invalid_metric(self, storage_backend):
        """Test aggregation with invalid metric."""
        with pytest.raises(ValueError, match="Unknown metric"):
            storage_backend.aggregate(metric="invalid_metric")

    def test_delete_old_events(self, storage_backend):
        """Test deleting old events."""
        now = datetime.now()
        old_time = now - timedelta(days=10)

        # Old event
        old_event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.01
        )
        old_event.timestamp = old_time
        storage_backend.save_event(old_event)

        # Recent event
        recent_event = TrackingEvent.create_llm_call(
            model="gpt-4", input_tokens=100, output_tokens=50, cost=0.02
        )
        storage_backend.save_event(recent_event)

        # Delete events older than 7 days
        deleted = storage_backend.delete_old_events(days=7)

        assert deleted == 1

        # Only recent event should remain
        results = storage_backend.query_events()
        assert len(results) == 1
        assert results[0].event_id == recent_event.event_id


# ============================================================================
# Storage Factory Tests
# ============================================================================


class TestStorageFactory:
    """Test create_storage factory function."""

    def test_create_memory_storage(self):
        """Test creating in-memory storage."""
        storage = create_storage("memory")
        assert isinstance(storage, InMemoryStorage)

    def test_create_sqlite_storage(self, temp_db_path):
        """Test creating SQLite storage."""
        storage = create_storage("sqlite", db_path=temp_db_path)
        assert isinstance(storage, SQLiteStorage)

    def test_create_sqlite_default_path(self):
        """Test creating SQLite storage with default path."""
        storage = create_storage("sqlite")
        assert isinstance(storage, SQLiteStorage)

    def test_create_invalid_backend(self):
        """Test creating storage with invalid backend type."""
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_storage("invalid_backend")

    def test_create_memory_storage_default(self):
        """Test that memory is the default backend."""
        storage = create_storage()
        assert isinstance(storage, InMemoryStorage)
