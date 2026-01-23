"""Storage backends for persistent tracking of LLM usage."""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class TrackingEvent:
    """Single tracking event for LLM usage.

    Attributes:
        event_id: Unique identifier for the event
        timestamp: When the event occurred
        event_type: Type of event (llm_call, workflow_start, workflow_end)
        model: Model used (e.g., gpt-4, claude-3-opus)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Cost in USD
        labels: Custom labels for filtering/grouping (agent_id, user_id, etc.)
        metadata: Additional metadata
        parent_id: Parent workflow/event ID for hierarchical tracking
    """

    event_id: str
    timestamp: datetime
    event_type: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    labels: Dict[str, str]
    metadata: Dict[str, Any]
    parent_id: Optional[str] = None

    @classmethod
    def create_llm_call(
        cls,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        **labels,
    ) -> "TrackingEvent":
        """Create an LLM call tracking event.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Cost in USD
            **labels: Custom labels (agent_id="my-agent", user_id="user-123", etc.)

        Returns:
            TrackingEvent instance

        Example:
            >>> event = TrackingEvent.create_llm_call(
            ...     model="gpt-4",
            ...     input_tokens=1000,
            ...     output_tokens=500,
            ...     cost=0.045,
            ...     agent_id="customer-support",
            ...     environment="production"
            ... )
        """
        return cls(
            event_id=str(uuid4()),
            timestamp=datetime.now(),
            event_type="llm_call",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            labels=labels,
            metadata={},
        )


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_event(self, event: TrackingEvent) -> None:
        """Save a tracking event.

        Args:
            event: Event to save
        """
        pass

    @abstractmethod
    def query_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[TrackingEvent]:
        """Query events with optional filters and time range.

        Args:
            filters: Filter conditions (e.g., {"agent_id": "my-agent"})
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of matching events
        """
        pass

    @abstractmethod
    def aggregate(
        self,
        metric: str,
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Aggregate metrics by dimensions.

        Args:
            metric: Metric to aggregate (cost, input_tokens, output_tokens, count)
            group_by: Dimensions to group by (e.g., ["agent_id", "model"])
            filters: Filter conditions
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dictionary with aggregated results

        Example:
            >>> results = storage.aggregate(
            ...     metric="cost",
            ...     group_by=["agent_id", "model"],
            ...     filters={"environment": "production"}
            ... )
            >>> # Returns: {
            >>> #   ("agent-1", "gpt-4"): 125.50,
            >>> #   ("agent-2", "gpt-4o-mini"): 5.25
            >>> # }
        """
        pass

    @abstractmethod
    def delete_old_events(self, days: int) -> int:
        """Delete events older than specified days.

        Args:
            days: Delete events older than this many days

        Returns:
            Number of events deleted
        """
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage backend for testing/development.

    Stores events in memory. Data is lost when process ends.
    Fast but not suitable for production.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self.events: List[TrackingEvent] = []

    def save_event(self, event: TrackingEvent) -> None:
        """Save event to memory."""
        self.events.append(event)

    def query_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[TrackingEvent]:
        """Query events from memory."""
        results = self.events

        # Apply time filters
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        # Apply label filters
        if filters:
            for key, value in filters.items():
                results = [e for e in results if e.labels.get(key) == value]

        # Apply pagination
        results = results[offset:]
        if limit:
            results = results[:limit]

        return results

    def aggregate(
        self,
        metric: str,
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Aggregate metrics in memory."""
        # First filter events
        events = self.query_events(filters, start_time, end_time)

        if not group_by:
            # Simple aggregation
            if metric == "cost":
                return {"total": sum(e.cost for e in events)}
            elif metric == "input_tokens":
                return {"total": sum(e.input_tokens for e in events)}
            elif metric == "output_tokens":
                return {"total": sum(e.output_tokens for e in events)}
            elif metric == "count":
                return {"total": len(events)}
            else:
                raise ValueError(f"Unknown metric: {metric}")

        # Group by dimensions
        groups: Dict[tuple, float] = {}
        for event in events:
            key = tuple(event.labels.get(dim, "unknown") for dim in group_by)
            if key not in groups:
                groups[key] = 0

            if metric == "cost":
                groups[key] += event.cost
            elif metric == "input_tokens":
                groups[key] += event.input_tokens
            elif metric == "output_tokens":
                groups[key] += event.output_tokens
            elif metric == "count":
                groups[key] += 1

        return groups

    def delete_old_events(self, days: int) -> int:
        """Delete old events from memory."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        old_count = len(self.events)
        self.events = [e for e in self.events if e.timestamp > cutoff]
        return old_count - len(self.events)


class SQLiteStorage(StorageBackend):
    """SQLite storage backend for single-machine production.

    Stores events in a SQLite database file. Suitable for production
    use on a single machine. Provides persistence and efficient querying.

    Args:
        db_path: Path to SQLite database file
    """

    def __init__(self, db_path: str = "token_calculator.db"):
        """Initialize SQLite storage.

        Args:
            db_path: Path to database file (created if doesn't exist)
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                parent_id TEXT,
                labels TEXT,
                metadata TEXT
            )
        """
        )

        # Create indexes for common queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_model ON events(model)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_parent_id ON events(parent_id)"
        )

        conn.commit()
        conn.close()

    def save_event(self, event: TrackingEvent) -> None:
        """Save event to SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events
            (event_id, timestamp, event_type, model, input_tokens,
             output_tokens, cost, parent_id, labels, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.event_id,
                event.timestamp.isoformat(),
                event.event_type,
                event.model,
                event.input_tokens,
                event.output_tokens,
                event.cost,
                event.parent_id,
                json.dumps(event.labels),
                json.dumps(event.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def query_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[TrackingEvent]:
        """Query events from SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM events WHERE 1=1"
        params = []

        # Add time filters
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        # Add label filters (using JSON extraction)
        if filters:
            for key, value in filters.items():
                query += f" AND json_extract(labels, '$.{key}') = ?"
                params.append(value)

        # Add ordering and pagination
        query += " ORDER BY timestamp DESC"
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to TrackingEvent objects
        events = []
        for row in rows:
            events.append(
                TrackingEvent(
                    event_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    event_type=row[2],
                    model=row[3],
                    input_tokens=row[4],
                    output_tokens=row[5],
                    cost=row[6],
                    parent_id=row[7],
                    labels=json.loads(row[8]),
                    metadata=json.loads(row[9]),
                )
            )

        return events

    def aggregate(
        self,
        metric: str,
        group_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Aggregate metrics using SQL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Map metric to SQL aggregate
        metric_map = {
            "cost": "SUM(cost)",
            "input_tokens": "SUM(input_tokens)",
            "output_tokens": "SUM(output_tokens)",
            "count": "COUNT(*)",
        }

        if metric not in metric_map:
            raise ValueError(f"Unknown metric: {metric}")

        agg_expr = metric_map[metric]

        if not group_by:
            # Simple aggregation
            query = f"SELECT {agg_expr} FROM events WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            if filters:
                for key, value in filters.items():
                    query += f" AND json_extract(labels, '$.{key}') = ?"
                    params.append(value)

            cursor.execute(query, params)
            result = cursor.fetchone()[0]
            conn.close()
            return {"total": result if result is not None else 0}

        # Group by dimensions
        group_exprs = [f"json_extract(labels, '$.{dim}')" for dim in group_by]
        group_clause = ", ".join(group_exprs)

        query = f"""
            SELECT {group_clause}, {agg_expr}
            FROM events
            WHERE 1=1
        """
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        if filters:
            for key, value in filters.items():
                query += f" AND json_extract(labels, '$.{key}') = ?"
                params.append(value)

        query += f" GROUP BY {group_clause}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert to dictionary
        results = {}
        for row in rows:
            key = tuple(row[:-1])  # All but last column are group dimensions
            value = row[-1]  # Last column is the aggregated value
            results[key] = value if value is not None else 0

        return results

    def delete_old_events(self, days: int) -> int:
        """Delete old events from SQLite."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM events WHERE timestamp < ?", (cutoff.isoformat(),)
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted


def create_storage(backend: str = "memory", **kwargs) -> StorageBackend:
    """Factory function to create storage backend.

    Args:
        backend: Backend type ("memory", "sqlite")
        **kwargs: Backend-specific arguments

    Returns:
        Storage backend instance

    Example:
        >>> storage = create_storage("sqlite", db_path="costs.db")
        >>> storage = create_storage("memory")
    """
    if backend == "memory":
        return InMemoryStorage()
    elif backend == "sqlite":
        db_path = kwargs.get("db_path", "token_calculator.db")
        return SQLiteStorage(db_path)
    else:
        raise ValueError(f"Unknown storage backend: {backend}")
