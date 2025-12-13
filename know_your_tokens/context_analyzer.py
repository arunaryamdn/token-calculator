"""
Context window analysis and management utilities.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from .models import get_model_config
from .tokenizer import TokenCounter


class ContextStatus(Enum):
    """Status of context window usage."""
    SAFE = "safe"  # < 70% usage
    WARNING = "warning"  # 70-90% usage
    CRITICAL = "critical"  # 90-100% usage
    EXCEEDED = "exceeded"  # > 100% usage


@dataclass
class ContextBreakdown:
    """Breakdown of context window usage."""
    total_tokens: int
    context_window: int
    max_output_tokens: int
    max_input_tokens: int
    available_for_output: int
    usage_percentage: float
    status: ContextStatus
    input_breakdown: Dict[str, int]
    warnings: List[str]
    recommendations: List[str]


class ContextAnalyzer:
    """
    Analyze context window usage and provide insights.
    """

    def __init__(self, model_name: str):
        """
        Initialize context analyzer for a specific model.

        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model_config = get_model_config(model_name)
        self.token_counter = TokenCounter(model_name)

    def analyze_messages(
        self,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, Any]]] = None,
        expected_output_tokens: Optional[int] = None,
    ) -> ContextBreakdown:
        """
        Analyze context window usage for a conversation.

        Args:
            messages: List of message dictionaries
            functions: Optional function definitions
            expected_output_tokens: Expected tokens in response (default: max_output_tokens)

        Returns:
            ContextBreakdown with detailed analysis
        """
        # Count tokens in messages
        token_breakdown = self.token_counter.count_messages(messages, include_function_tokens=True)

        # Count function definition tokens
        function_tokens = 0
        if functions:
            function_tokens = self.token_counter.count_function_definitions(functions)

        # Total input tokens
        total_input_tokens = token_breakdown['total'] + function_tokens

        # Expected output tokens
        if expected_output_tokens is None:
            expected_output_tokens = self.model_config.max_output_tokens

        # Calculate available space
        total_tokens = total_input_tokens + expected_output_tokens
        available_for_output = self.model_config.context_window - total_input_tokens

        # Calculate usage percentage
        usage_percentage = (total_input_tokens / self.model_config.context_window) * 100

        # Determine status
        status = self._determine_status(usage_percentage, total_tokens)

        # Generate warnings and recommendations
        warnings = self._generate_warnings(
            total_input_tokens,
            total_tokens,
            available_for_output,
            expected_output_tokens,
            token_breakdown
        )

        recommendations = self._generate_recommendations(
            total_input_tokens,
            token_breakdown,
            available_for_output
        )

        # Create input breakdown
        input_breakdown = {
            'system_messages': token_breakdown.get('system', 0),
            'user_messages': token_breakdown.get('user', 0),
            'assistant_messages': token_breakdown.get('assistant', 0),
            'function_calls': token_breakdown.get('functions', 0),
            'function_definitions': function_tokens,
            'formatting_overhead': token_breakdown.get('overhead', 0),
        }

        return ContextBreakdown(
            total_tokens=total_input_tokens,
            context_window=self.model_config.context_window,
            max_output_tokens=self.model_config.max_output_tokens,
            max_input_tokens=self.model_config.max_input_tokens,
            available_for_output=available_for_output,
            usage_percentage=usage_percentage,
            status=status,
            input_breakdown=input_breakdown,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _determine_status(self, usage_percentage: float, total_tokens: int) -> ContextStatus:
        """Determine context status based on usage."""
        if total_tokens > self.model_config.context_window:
            return ContextStatus.EXCEEDED
        elif usage_percentage >= 90:
            return ContextStatus.CRITICAL
        elif usage_percentage >= 70:
            return ContextStatus.WARNING
        else:
            return ContextStatus.SAFE

    def _generate_warnings(
        self,
        total_input_tokens: int,
        total_tokens: int,
        available_for_output: int,
        expected_output_tokens: int,
        token_breakdown: Dict[str, int]
    ) -> List[str]:
        """Generate warnings based on context usage."""
        warnings = []

        # Context exceeded
        if total_tokens > self.model_config.context_window:
            overflow = total_tokens - self.model_config.context_window
            warnings.append(
                f"⚠️ CRITICAL: Context window exceeded by {overflow} tokens! "
                f"The model will not accept this request."
            )

        # Not enough space for expected output
        if available_for_output < expected_output_tokens:
            shortage = expected_output_tokens - available_for_output
            warnings.append(
                f"⚠️ WARNING: Not enough space for expected output. "
                f"Short by {shortage} tokens. Output may be truncated."
            )

        # High usage
        usage_pct = (total_input_tokens / self.model_config.context_window) * 100
        if usage_pct >= 90:
            warnings.append(
                f"⚠️ CRITICAL: Using {usage_pct:.1f}% of context window. "
                "Risk of context breaks and reduced accuracy."
            )
        elif usage_pct >= 70:
            warnings.append(
                f"⚠️ WARNING: Using {usage_pct:.1f}% of context window. "
                "Consider reducing context to avoid issues."
            )

        # Large assistant messages (potential context rot)
        if token_breakdown.get('assistant', 0) > self.model_config.context_window * 0.3:
            warnings.append(
                "⚠️ Assistant messages consume >30% of context. "
                "This may indicate context rot in long conversations."
            )

        return warnings

    def _generate_recommendations(
        self,
        total_input_tokens: int,
        token_breakdown: Dict[str, int],
        available_for_output: int
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # High system message usage
        system_tokens = token_breakdown.get('system', 0)
        if system_tokens > 2000:
            recommendations.append(
                f"💡 System message uses {system_tokens} tokens. "
                "Consider shortening system instructions."
            )

        # Many user messages (conversation history)
        user_tokens = token_breakdown.get('user', 0)
        if user_tokens > self.model_config.context_window * 0.4:
            recommendations.append(
                f"💡 User messages use {user_tokens} tokens ({user_tokens / self.model_config.context_window * 100:.1f}%). "
                "Consider using conversation summarization."
            )

        # Function overhead
        func_tokens = token_breakdown.get('functions', 0)
        if func_tokens > 1000:
            recommendations.append(
                f"💡 Function calls/definitions use {func_tokens} tokens. "
                "Consider reducing number of available functions."
            )

        # Limited output space
        if available_for_output < self.model_config.max_output_tokens * 0.5:
            recommendations.append(
                f"💡 Only {available_for_output} tokens available for output. "
                "Reduce input context to allow longer responses."
            )

        return recommendations

    def estimate_max_turns(
        self,
        avg_user_tokens: int,
        avg_assistant_tokens: int,
        system_tokens: int = 0,
        rag_tokens: int = 0,
        function_tokens: int = 0,
    ) -> Dict[str, Any]:
        """
        Estimate maximum conversation turns before context limit.

        Args:
            avg_user_tokens: Average tokens per user message
            avg_assistant_tokens: Average tokens per assistant response
            system_tokens: Tokens in system message
            rag_tokens: Tokens used for RAG context
            function_tokens: Tokens used for function definitions

        Returns:
            Dictionary with:
            - max_turns: Maximum conversation turns
            - tokens_per_turn: Tokens consumed per turn
            - fixed_overhead: Fixed tokens (system, RAG, functions)
            - breakdown: Detailed breakdown
        """
        # Fixed overhead
        fixed_overhead = system_tokens + rag_tokens + function_tokens

        # Tokens per conversation turn
        tokens_per_turn = avg_user_tokens + avg_assistant_tokens + 8  # +8 for message formatting

        # Available space for conversation
        available_for_conversation = self.model_config.max_input_tokens - fixed_overhead

        # Maximum turns
        max_turns = available_for_conversation // tokens_per_turn

        # Calculate when warnings should trigger
        warning_threshold = int(max_turns * 0.7)
        critical_threshold = int(max_turns * 0.9)

        return {
            'max_turns': max_turns,
            'tokens_per_turn': tokens_per_turn,
            'fixed_overhead': fixed_overhead,
            'available_for_conversation': available_for_conversation,
            'warning_at_turn': warning_threshold,
            'critical_at_turn': critical_threshold,
            'breakdown': {
                'system': system_tokens,
                'rag': rag_tokens,
                'functions': function_tokens,
                'per_user_message': avg_user_tokens,
                'per_assistant_message': avg_assistant_tokens,
                'formatting_per_turn': 8,
            }
        }

    def find_optimal_context_split(
        self,
        messages: List[Dict[str, Any]],
        keep_recent: int = 5,
    ) -> Dict[str, Any]:
        """
        Find optimal way to split context when limit is reached.

        Args:
            messages: List of messages
            keep_recent: Number of recent messages to always keep

        Returns:
            Dictionary with split recommendations
        """
        if len(messages) <= keep_recent:
            return {
                'needs_split': False,
                'total_messages': len(messages),
                'kept_messages': len(messages),
            }

        # Count tokens for each message
        message_tokens = []
        for msg in messages:
            tokens = self.token_counter.count_tokens(str(msg.get('content', '')))
            message_tokens.append(tokens)

        # Always keep system message (if present) and recent messages
        system_messages = [i for i, msg in enumerate(messages) if msg.get('role') == 'system']
        recent_indices = list(range(len(messages) - keep_recent, len(messages)))

        # Combine indices to keep
        keep_indices = set(system_messages + recent_indices)

        # Calculate tokens for kept messages
        kept_tokens = sum(message_tokens[i] for i in keep_indices)

        # See if we can add more messages
        available_space = self.model_config.max_input_tokens - kept_tokens
        additional_messages = []

        # Try to add messages from middle (oldest to newest, excluding kept)
        for i in range(len(messages)):
            if i not in keep_indices:
                if message_tokens[i] <= available_space:
                    additional_messages.append(i)
                    available_space -= message_tokens[i]

        final_kept_indices = sorted(list(keep_indices) + additional_messages)

        return {
            'needs_split': len(final_kept_indices) < len(messages),
            'total_messages': len(messages),
            'kept_messages': len(final_kept_indices),
            'removed_messages': len(messages) - len(final_kept_indices),
            'kept_indices': final_kept_indices,
            'total_tokens_before': sum(message_tokens),
            'total_tokens_after': sum(message_tokens[i] for i in final_kept_indices),
            'tokens_saved': sum(message_tokens) - sum(message_tokens[i] for i in final_kept_indices),
        }
