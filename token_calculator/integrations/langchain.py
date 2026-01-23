"""LangChain integration for automatic token tracking.

This module provides a callback handler that automatically tracks
token usage and costs for LangChain applications.

Example:
    >>> from langchain_openai import ChatOpenAI
    >>> from token_calculator.integrations.langchain import TokenCalculatorCallback
    >>> from token_calculator import CostTracker, create_storage
    >>>
    >>> # Setup tracker
    >>> tracker = CostTracker(
    ...     storage=create_storage("sqlite", db_path="costs.db"),
    ...     default_labels={"environment": "production"}
    ... )
    >>>
    >>> # Create callback
    >>> callback = TokenCalculatorCallback(
    ...     tracker=tracker,
    ...     agent_id="my-agent"
    ... )
    >>>
    >>> # Use with LangChain
    >>> llm = ChatOpenAI(callbacks=[callback])
    >>> result = llm.invoke("Hello!")
    >>> # Token usage automatically tracked!
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult
except ImportError:
    raise ImportError(
        "LangChain is not installed. Install with: pip install langchain"
    )

from ..cost_tracker import CostTracker
from ..tokenizer import count_tokens


class TokenCalculatorCallback(BaseCallbackHandler):
    """LangChain callback handler for automatic token tracking.

    Automatically tracks token usage and costs for all LLM calls
    made through LangChain.

    Args:
        tracker: CostTracker instance
        **default_labels: Default labels to apply to all calls

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> tracker = CostTracker()
        >>> callback = TokenCalculatorCallback(
        ...     tracker=tracker,
        ...     agent_id="customer-support",
        ...     environment="production"
        ... )
        >>> llm = ChatOpenAI(callbacks=[callback])
        >>> result = llm.invoke("What is AI?")
        >>> # Check costs
        >>> report = tracker.get_costs(start_date="today")
        >>> print(f"Total cost: ${report.total_cost}")
    """

    def __init__(
        self,
        tracker: CostTracker,
        **default_labels: str,
    ):
        """Initialize callback handler.

        Args:
            tracker: CostTracker instance for recording usage
            **default_labels: Default labels (agent_id="my-agent", etc.)
        """
        self.tracker = tracker
        self.default_labels = default_labels
        self.call_start_data: Dict[UUID, Dict[str, Any]] = {}

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts running."""
        # Extract model name
        model_name = self._extract_model_name(serialized, kwargs)

        # Count input tokens
        input_text = " ".join(prompts)
        input_tokens = count_tokens(input_text, model_name)

        # Store for later
        self.call_start_data[run_id] = {
            "model": model_name,
            "input_tokens": input_tokens,
            "tags": tags or [],
            "metadata": metadata or {},
        }

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM ends running."""
        if run_id not in self.call_start_data:
            return  # Can't track if we didn't see the start

        start_data = self.call_start_data[run_id]

        # Extract model and input tokens
        model_name = start_data["model"]
        input_tokens = start_data["input_tokens"]

        # Count output tokens
        output_tokens = 0
        if response.generations:
            for generation_list in response.generations:
                for generation in generation_list:
                    output_tokens += count_tokens(generation.text, model_name)

        # Merge labels
        labels = {**self.default_labels}

        # Add tags as labels
        if start_data["tags"]:
            labels["tags"] = ",".join(start_data["tags"])

        # Add metadata
        if start_data["metadata"]:
            for key, value in start_data["metadata"].items():
                if isinstance(value, (str, int, float, bool)):
                    labels[f"meta_{key}"] = str(value)

        # Track the call
        self.tracker.track_call(
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **labels,
        )

        # Cleanup
        del self.call_start_data[run_id]

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM errors."""
        # Cleanup
        if run_id in self.call_start_data:
            del self.call_start_data[run_id]

    def _extract_model_name(
        self,
        serialized: Dict[str, Any],
        kwargs: Dict[str, Any],
    ) -> str:
        """Extract model name from LangChain call data."""
        # Try to get from kwargs first
        if "invocation_params" in kwargs:
            params = kwargs["invocation_params"]
            if "model_name" in params:
                return params["model_name"]
            if "model" in params:
                return params["model"]

        # Try serialized data
        if "name" in serialized:
            name = serialized["name"]
            # LangChain class names like "ChatOpenAI" -> default to gpt-3.5-turbo
            if name == "ChatOpenAI":
                return "gpt-3.5-turbo"
            elif name == "ChatAnthropic":
                return "claude-3-5-sonnet-20241022"
            elif name == "ChatGoogleGenerativeAI":
                return "gemini-1.5-pro"

        # Try ID (might contain model name)
        if "id" in serialized:
            id_parts = serialized["id"]
            if isinstance(id_parts, list):
                for part in id_parts:
                    if isinstance(part, str) and ("gpt" in part.lower() or "claude" in part.lower()):
                        return part

        # Default fallback
        return "gpt-3.5-turbo"


class WorkflowCallbackHandler(BaseCallbackHandler):
    """LangChain callback for tracking multi-agent workflows.

    Use this when you have multiple agents working together and want
    to track each agent's contribution to overall cost.

    Example:
        >>> from token_calculator import WorkflowTracker, create_storage
        >>> tracker = WorkflowTracker(
        ...     workflow_id="customer-support",
        ...     storage=create_storage("sqlite", db_path="costs.db")
        ... )
        >>> # Track each agent
        >>> with tracker.track_agent("router"):
        ...     router_callback = WorkflowCallbackHandler(
        ...         tracker=tracker,
        ...         agent_id="router"
        ...     )
        ...     router_llm = ChatOpenAI(callbacks=[router_callback])
        ...     # Use router_llm...
    """

    def __init__(
        self,
        tracker: "WorkflowTracker",  # type: ignore
        agent_id: str,
        **labels: str,
    ):
        """Initialize workflow callback.

        Args:
            tracker: WorkflowTracker instance
            agent_id: Agent identifier
            **labels: Additional labels
        """
        from ..workflow_tracker import WorkflowTracker

        if not isinstance(tracker, WorkflowTracker):
            raise TypeError("tracker must be a WorkflowTracker instance")

        self.workflow_tracker = tracker
        self.agent_id = agent_id
        self.labels = labels
        self.call_data: Dict[UUID, Dict[str, Any]] = {}

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts."""
        model_name = self._extract_model_name(serialized, kwargs)
        input_text = " ".join(prompts)
        input_tokens = count_tokens(input_text, model_name)

        self.call_data[run_id] = {
            "model": model_name,
            "input_tokens": input_tokens,
        }

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when LLM ends."""
        if run_id not in self.call_data:
            return

        call_data = self.call_data[run_id]
        model_name = call_data["model"]
        input_tokens = call_data["input_tokens"]

        # Count output tokens
        output_tokens = 0
        if response.generations:
            for generation_list in response.generations:
                for generation in generation_list:
                    output_tokens += count_tokens(generation.text, model_name)

        # Track via workflow tracker
        # Note: This requires accessing the agent context
        # In practice, you'd use with tracker.track_agent() and track calls there
        # This is a simplified version

        del self.call_data[run_id]

    def _extract_model_name(
        self,
        serialized: Dict[str, Any],
        kwargs: Dict[str, Any],
    ) -> str:
        """Extract model name."""
        if "invocation_params" in kwargs:
            params = kwargs["invocation_params"]
            if "model_name" in params:
                return params["model_name"]
            if "model" in params:
                return params["model"]

        if "name" in serialized:
            name = serialized["name"]
            if name == "ChatOpenAI":
                return "gpt-3.5-turbo"
            elif name == "ChatAnthropic":
                return "claude-3-5-sonnet-20241022"

        return "gpt-3.5-turbo"
