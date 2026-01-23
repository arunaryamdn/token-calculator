"""Multi-agent workflow tracking and analysis."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .cost_tracker import CostTracker
from .storage import InMemoryStorage, StorageBackend, TrackingEvent


@dataclass
class AgentExecution:
    """Record of a single agent's execution within a workflow.

    Attributes:
        agent_id: Agent identifier
        start_time: When agent started
        end_time: When agent finished
        input_tokens: Tokens consumed by this agent
        output_tokens: Tokens produced by this agent
        cost: Cost of this agent's execution
        model: Model used by this agent
        metadata: Additional metadata
    """

    agent_id: str
    start_time: datetime
    end_time: Optional[datetime]
    input_tokens: int
    output_tokens: int
    cost: float
    model: str
    metadata: Dict[str, Any]


@dataclass
class WorkflowAnalysis:
    """Analysis of a multi-agent workflow.

    Attributes:
        workflow_id: Workflow identifier
        total_cost: Total cost across all agents
        total_input_tokens: Total input tokens
        total_output_tokens: Total output tokens
        duration_seconds: Workflow duration in seconds
        agents: List of agent executions
        bottleneck_agent: Agent that consumed most tokens/cost
        token_breakdown: Token breakdown by agent
        cost_breakdown: Cost breakdown by agent
        efficiency_score: Efficiency score (0-100)
        recommendations: Optimization recommendations
    """

    workflow_id: str
    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    duration_seconds: float
    agents: List[AgentExecution]
    bottleneck_agent: Optional[str]
    token_breakdown: Dict[str, int]
    cost_breakdown: Dict[str, float]
    efficiency_score: float
    recommendations: List[str]

    def __str__(self) -> str:
        """String representation of workflow analysis."""
        lines = [
            f"Workflow Analysis: {self.workflow_id}",
            f"  Total Cost: ${self.total_cost:.4f}",
            f"  Total Tokens: {self.total_input_tokens + self.total_output_tokens:,}",
            f"  Duration: {self.duration_seconds:.2f}s",
            f"  Agents: {len(self.agents)}",
        ]

        if self.bottleneck_agent:
            bottleneck_cost = self.cost_breakdown.get(self.bottleneck_agent, 0)
            lines.append(
                f"  Bottleneck: {self.bottleneck_agent} (${bottleneck_cost:.4f})"
            )

        lines.append(f"  Efficiency: {self.efficiency_score:.0f}/100")

        if self.cost_breakdown:
            lines.append("\n  Cost Breakdown:")
            for agent, cost in sorted(
                self.cost_breakdown.items(), key=lambda x: x[1], reverse=True
            ):
                pct = (cost / self.total_cost * 100) if self.total_cost > 0 else 0
                lines.append(f"    {agent}: ${cost:.4f} ({pct:.1f}%)")

        if self.recommendations:
            lines.append("\n  Recommendations:")
            for rec in self.recommendations:
                lines.append(f"    • {rec}")

        return "\n".join(lines)


@dataclass
class OptimizationSuggestion:
    """Optimization suggestion for a workflow.

    Attributes:
        title: Short title
        description: Detailed description
        estimated_savings: Estimated cost savings per workflow execution
        confidence: Confidence level (0-1)
        impact: Impact level (high, medium, low)
    """

    title: str
    description: str
    estimated_savings: float
    confidence: float
    impact: str

    def __str__(self) -> str:
        """String representation."""
        impact_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        emoji = impact_emoji.get(self.impact, "⚪")

        return (
            f"{emoji} {self.title}\n"
            f"   {self.description}\n"
            f"   Savings: ${self.estimated_savings:.4f}/execution\n"
            f"   Confidence: {self.confidence*100:.0f}%"
        )


class WorkflowTracker:
    """Track multi-agent workflows with detailed cost attribution.

    Enables tracking of complex multi-agent workflows where multiple agents
    work together to accomplish a task. Provides detailed cost attribution,
    bottleneck identification, and optimization recommendations.

    Args:
        workflow_id: Unique workflow identifier
        storage: Storage backend for persisting events
        **default_labels: Default labels to apply to all events

    Example:
        >>> from token_calculator import WorkflowTracker, create_storage
        >>> tracker = WorkflowTracker(
        ...     workflow_id="customer-support-v2",
        ...     storage=create_storage("sqlite", db_path="costs.db")
        ... )
        >>> with tracker.track_agent("planner", model="gpt-4o"):
        ...     result = planner.run(query)  # Your agent code
        >>> with tracker.track_agent("executor", model="gpt-4"):
        ...     final = executor.run(result)
        >>> analysis = tracker.analyze()
        >>> print(analysis)
    """

    def __init__(
        self,
        workflow_id: str,
        storage: Optional[StorageBackend] = None,
        **default_labels,
    ):
        """Initialize workflow tracker.

        Args:
            workflow_id: Unique workflow identifier
            storage: Storage backend (defaults to in-memory)
            **default_labels: Default labels for all events
        """
        self.workflow_id = workflow_id
        self.storage = storage or InMemoryStorage()
        self.default_labels = default_labels

        # Track workflow start
        self.start_time = datetime.now()
        self.current_agent: Optional[str] = None
        self.agent_start_time: Optional[datetime] = None

        # Store agent execution stats
        self.agent_executions: List[AgentExecution] = []

    @contextmanager
    def track_agent(
        self,
        agent_id: str,
        model: Optional[str] = None,
        **labels,
    ):
        """Context manager to track an agent's execution.

        Args:
            agent_id: Agent identifier
            model: Model used by this agent (if known)
            **labels: Additional labels for this agent's events

        Yields:
            AgentContext for tracking LLM calls within this agent

        Example:
            >>> with tracker.track_agent("planner", model="gpt-4o"):
            ...     # Your agent code here
            ...     response = agent.run(input)
            ...     # Track LLM calls
            ...     context.track_call(
            ...         input_tokens=1000,
            ...         output_tokens=500
            ...     )
        """
        self.current_agent = agent_id
        self.agent_start_time = datetime.now()

        # Yield agent context for tracking calls
        agent_context = AgentContext(
            workflow_id=self.workflow_id,
            agent_id=agent_id,
            model=model,
            storage=self.storage,
            labels={**self.default_labels, **labels},
        )

        try:
            yield agent_context
        finally:
            # Agent execution completed
            end_time = datetime.now()

            # Get agent's events
            agent_events = self.storage.query_events(
                filters={
                    "workflow_id": self.workflow_id,
                    "agent_id": agent_id,
                },
                start_time=self.agent_start_time,
                end_time=end_time,
            )

            # Calculate agent stats
            total_input = sum(e.input_tokens for e in agent_events)
            total_output = sum(e.output_tokens for e in agent_events)
            total_cost = sum(e.cost for e in agent_events)
            agent_model = agent_events[0].model if agent_events else model or "unknown"

            # Record agent execution
            execution = AgentExecution(
                agent_id=agent_id,
                start_time=self.agent_start_time,
                end_time=end_time,
                input_tokens=total_input,
                output_tokens=total_output,
                cost=total_cost,
                model=agent_model,
                metadata={**self.default_labels, **labels},
            )

            self.agent_executions.append(execution)
            self.current_agent = None

    def analyze(self) -> WorkflowAnalysis:
        """Analyze the workflow and generate insights.

        Returns:
            WorkflowAnalysis with detailed metrics and recommendations

        Example:
            >>> analysis = tracker.analyze()
            >>> print(f"Total cost: ${analysis.total_cost}")
            >>> print(f"Bottleneck: {analysis.bottleneck_agent}")
            >>> for rec in analysis.recommendations:
            ...     print(f"  • {rec}")
        """
        if not self.agent_executions:
            return WorkflowAnalysis(
                workflow_id=self.workflow_id,
                total_cost=0,
                total_input_tokens=0,
                total_output_tokens=0,
                duration_seconds=0,
                agents=[],
                bottleneck_agent=None,
                token_breakdown={},
                cost_breakdown={},
                efficiency_score=0,
                recommendations=["No agent executions tracked"],
            )

        # Calculate totals
        total_cost = sum(a.cost for a in self.agent_executions)
        total_input = sum(a.input_tokens for a in self.agent_executions)
        total_output = sum(a.output_tokens for a in self.agent_executions)

        # Calculate duration
        end_time = max(
            a.end_time for a in self.agent_executions if a.end_time is not None
        )
        duration = (end_time - self.start_time).total_seconds()

        # Build breakdowns
        token_breakdown = {}
        cost_breakdown = {}

        for agent in self.agent_executions:
            token_breakdown[agent.agent_id] = (
                agent.input_tokens + agent.output_tokens
            )
            cost_breakdown[agent.agent_id] = agent.cost

        # Identify bottleneck (highest cost)
        bottleneck = max(cost_breakdown.items(), key=lambda x: x[1])[0]

        # Calculate efficiency score
        efficiency = self._calculate_efficiency()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return WorkflowAnalysis(
            workflow_id=self.workflow_id,
            total_cost=total_cost,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            duration_seconds=duration,
            agents=self.agent_executions,
            bottleneck_agent=bottleneck,
            token_breakdown=token_breakdown,
            cost_breakdown=cost_breakdown,
            efficiency_score=efficiency,
            recommendations=recommendations,
        )

    def suggest_optimizations(self) -> List[OptimizationSuggestion]:
        """Suggest optimizations for the workflow.

        Returns:
            List of optimization suggestions

        Example:
            >>> suggestions = tracker.suggest_optimizations()
            >>> for suggestion in suggestions:
            ...     print(suggestion)
        """
        analysis = self.analyze()
        suggestions = []

        # Suggestion 1: Expensive bottleneck
        if analysis.bottleneck_agent:
            bottleneck_cost = analysis.cost_breakdown[analysis.bottleneck_agent]
            if bottleneck_cost / analysis.total_cost > 0.5:  # >50% of cost
                bottleneck_agent = next(
                    a for a in analysis.agents if a.agent_id == analysis.bottleneck_agent
                )

                suggestions.append(
                    OptimizationSuggestion(
                        title=f"Optimize {analysis.bottleneck_agent}",
                        description=(
                            f"{analysis.bottleneck_agent} accounts for "
                            f"{bottleneck_cost/analysis.total_cost*100:.0f}% of workflow cost. "
                            f"Consider using a cheaper model or reducing prompt size."
                        ),
                        estimated_savings=bottleneck_cost * 0.3,  # Assume 30% savings
                        confidence=0.7,
                        impact="high",
                    )
                )

        # Suggestion 2: Parallel execution opportunities
        if len(analysis.agents) > 1:
            # Check if agents could run in parallel
            sequential_agents = []
            for i, agent in enumerate(analysis.agents[:-1]):
                next_agent = analysis.agents[i + 1]
                if next_agent.start_time > agent.end_time:
                    sequential_agents.append((agent.agent_id, next_agent.agent_id))

            if sequential_agents:
                suggestions.append(
                    OptimizationSuggestion(
                        title="Consider parallel execution",
                        description=(
                            f"Some agents run sequentially. If they're independent, "
                            f"running in parallel could reduce latency."
                        ),
                        estimated_savings=0,  # Latency improvement, not cost
                        confidence=0.5,
                        impact="medium",
                    )
                )

        # Suggestion 3: Context sharing opportunities
        # Check if multiple agents use similar context
        if len(analysis.agents) > 1:
            # Simple heuristic: if agents have similar token counts, they might share context
            token_counts = [a.input_tokens for a in analysis.agents]
            avg_tokens = sum(token_counts) / len(token_counts)

            high_token_agents = [
                a for a in analysis.agents if a.input_tokens > avg_tokens * 1.5
            ]

            if len(high_token_agents) > 1:
                # Estimate overlap savings
                overlap_savings = sum(a.cost * 0.2 for a in high_token_agents)

                suggestions.append(
                    OptimizationSuggestion(
                        title="Potential context overlap",
                        description=(
                            f"Multiple agents have high input token counts. "
                            f"They may share context that could be deduplicated."
                        ),
                        estimated_savings=overlap_savings,
                        confidence=0.4,
                        impact="medium",
                    )
                )

        # Sort by estimated savings
        suggestions.sort(key=lambda s: s.estimated_savings, reverse=True)
        return suggestions

    def visualize(self) -> str:
        """Generate ASCII visualization of workflow.

        Returns:
            ASCII art showing workflow execution

        Example:
            >>> print(tracker.visualize())
            Workflow: customer-support-v2
            ┌─────────────────────────────────────────┐
            │ planner (gpt-4o)                        │
            │ Cost: $0.0150 | Tokens: 1500            │
            └─────────────────────────────────────────┘
                           ↓
            ┌─────────────────────────────────────────┐
            │ executor (gpt-4)                        │
            │ Cost: $0.0450 | Tokens: 3000            │
            └─────────────────────────────────────────┘
        """
        if not self.agent_executions:
            return f"Workflow: {self.workflow_id}\n(No agents executed)"

        lines = [f"Workflow: {self.workflow_id}"]

        for agent in self.agent_executions:
            total_tokens = agent.input_tokens + agent.output_tokens

            # Create box for agent
            lines.append("┌─────────────────────────────────────────┐")
            lines.append(
                f"│ {agent.agent_id:<20} ({agent.model:<15}) │"[:43] + "│"
            )
            lines.append(
                f"│ Cost: ${agent.cost:.4f} | Tokens: {total_tokens:<10} │"[:43] + "│"
            )
            lines.append("└─────────────────────────────────────────┘")
            lines.append("             ↓")

        # Remove last arrow
        lines = lines[:-1]

        return "\n".join(lines)

    def _calculate_efficiency(self) -> float:
        """Calculate workflow efficiency score (0-100).

        Considers:
        - Token usage efficiency
        - Cost distribution balance
        - Execution time
        """
        if not self.agent_executions:
            return 0

        # Factor 1: Cost distribution (more balanced = better)
        total_cost = sum(a.cost for a in self.agent_executions)
        if total_cost == 0:
            return 0

        cost_distribution = [a.cost / total_cost for a in self.agent_executions]
        # Entropy-based measure of balance
        import math

        entropy = -sum(
            p * math.log(p) if p > 0 else 0 for p in cost_distribution
        )
        max_entropy = math.log(len(self.agent_executions))
        balance_score = entropy / max_entropy if max_entropy > 0 else 0

        # Factor 2: Token efficiency (lower tokens = better for same task)
        # This is a simplified heuristic
        total_tokens = sum(
            a.input_tokens + a.output_tokens for a in self.agent_executions
        )
        # Assume baseline of 10k tokens for a multi-agent workflow
        token_score = max(0, 100 - (total_tokens / 100))

        # Combine factors
        efficiency = (balance_score * 50) + (min(token_score, 50))

        return min(100, max(0, efficiency))

    def _generate_recommendations(self) -> List[str]:
        """Generate workflow optimization recommendations."""
        recommendations = []

        if not self.agent_executions:
            return ["No data available for recommendations"]

        # Check for expensive bottleneck
        total_cost = sum(a.cost for a in self.agent_executions)
        for agent in self.agent_executions:
            if agent.cost / total_cost > 0.5:
                recommendations.append(
                    f"{agent.agent_id} accounts for >50% of cost. Consider optimization."
                )

        # Check for high token usage
        for agent in self.agent_executions:
            if agent.input_tokens > 10000:
                recommendations.append(
                    f"{agent.agent_id} uses {agent.input_tokens} input tokens. "
                    "Consider context compression."
                )

        # Check for potential parallelization
        if len(self.agent_executions) > 1:
            recommendations.append(
                "Review if any agents can run in parallel to reduce latency."
            )

        return recommendations if recommendations else ["Workflow looks efficient!"]


class AgentContext:
    """Context for tracking LLM calls within an agent.

    This is yielded by WorkflowTracker.track_agent() and allows
    tracking individual LLM calls within an agent's execution.
    """

    def __init__(
        self,
        workflow_id: str,
        agent_id: str,
        model: Optional[str],
        storage: StorageBackend,
        labels: Dict[str, str],
    ):
        """Initialize agent context."""
        self.workflow_id = workflow_id
        self.agent_id = agent_id
        self.model = model
        self.storage = storage
        self.labels = labels
        self.cost_tracker = CostTracker(
            storage=storage,
            default_labels={
                **labels,
                "workflow_id": workflow_id,
                "agent_id": agent_id,
            },
        )

    def track_call(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None,
        **extra_labels,
    ):
        """Track an LLM call within this agent.

        Args:
            input_tokens: Input tokens for this call
            output_tokens: Output tokens for this call
            model: Model used (overrides agent's default model)
            **extra_labels: Additional labels for this call
        """
        call_model = model or self.model
        if not call_model:
            raise ValueError(
                "Model must be specified either in track_agent() or track_call()"
            )

        self.cost_tracker.track_call(
            model=call_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **extra_labels,
        )
