"""
Conversation manager for tracking multi-turn chats and context usage.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .models import get_model_config
from .tokenizer import TokenCounter
from .context_analyzer import ContextAnalyzer, ContextStatus
from .cost_calculator import CostCalculator


class MessageRole(Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    user_message: str
    assistant_response: str
    user_tokens: int
    assistant_tokens: int
    total_tokens: int
    cost: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationStats:
    """Statistics for a conversation."""
    total_turns: int
    total_tokens: int
    total_cost: float
    input_tokens: int
    output_tokens: int
    context_status: ContextStatus
    context_usage_percentage: float
    estimated_turns_remaining: int
    warnings: List[str]


class ConversationManager:
    """
    Manage multi-turn conversations with context tracking.
    """

    def __init__(
        self,
        model_name: str,
        system_message: Optional[str] = None,
        rag_context: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize conversation manager.

        Args:
            model_name: Name of the model
            system_message: Optional system message
            rag_context: Optional RAG/knowledge base context
            functions: Optional function definitions
        """
        self.model_name = model_name
        self.model_config = get_model_config(model_name)
        self.token_counter = TokenCounter(model_name)
        self.context_analyzer = ContextAnalyzer(model_name)
        self.cost_calculator = CostCalculator(model_name)

        # Conversation state
        self.messages: List[Dict[str, Any]] = []
        self.turns: List[ConversationTurn] = []
        self.functions = functions or []
        self.rag_context = rag_context or ""

        # Add system message if provided
        if system_message:
            self.messages.append({
                'role': MessageRole.SYSTEM.value,
                'content': system_message,
            })

        # Calculate fixed overhead
        self.fixed_overhead = self._calculate_fixed_overhead()

    def _calculate_fixed_overhead(self) -> int:
        """Calculate fixed token overhead (system, RAG, functions)."""
        overhead = 0

        # System message tokens
        if self.messages:
            for msg in self.messages:
                if msg.get('role') == MessageRole.SYSTEM.value:
                    overhead += self.token_counter.count_tokens(msg.get('content', ''))

        # RAG context tokens
        if self.rag_context:
            overhead += self.token_counter.count_tokens(self.rag_context)

        # Function definition tokens
        if self.functions:
            overhead += self.token_counter.count_function_definitions(self.functions)

        return overhead

    def add_turn(
        self,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationTurn:
        """
        Add a conversation turn.

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata for this turn

        Returns:
            ConversationTurn object
        """
        # Count tokens
        user_tokens = self.token_counter.count_tokens(user_message)
        assistant_tokens = self.token_counter.count_tokens(assistant_response)
        total_tokens = user_tokens + assistant_tokens

        # Calculate cost
        cost_breakdown = self.cost_calculator.calculate_cost(
            user_tokens,
            assistant_tokens,
        )

        # Create turn object
        turn = ConversationTurn(
            user_message=user_message,
            assistant_response=assistant_response,
            user_tokens=user_tokens,
            assistant_tokens=assistant_tokens,
            total_tokens=total_tokens,
            cost=cost_breakdown.total_cost,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        # Add to messages
        self.messages.append({
            'role': MessageRole.USER.value,
            'content': user_message,
        })
        self.messages.append({
            'role': MessageRole.ASSISTANT.value,
            'content': assistant_response,
        })

        # Add to turns
        self.turns.append(turn)

        return turn

    def get_stats(self) -> ConversationStats:
        """
        Get current conversation statistics.

        Returns:
            ConversationStats object
        """
        # Analyze context
        analysis = self.context_analyzer.analyze_messages(
            self.messages,
            functions=self.functions if self.functions else None,
        )

        # Calculate totals
        total_tokens = sum(turn.total_tokens for turn in self.turns)
        total_cost = sum(turn.cost for turn in self.turns)
        input_tokens = sum(turn.user_tokens for turn in self.turns)
        output_tokens = sum(turn.assistant_tokens for turn in self.turns)

        # Estimate remaining turns
        if self.turns:
            avg_tokens_per_turn = total_tokens / len(self.turns)
            available_tokens = self.model_config.context_window - analysis.total_tokens
            estimated_remaining = int(available_tokens / avg_tokens_per_turn) if avg_tokens_per_turn > 0 else 0
        else:
            estimated_remaining = 0

        return ConversationStats(
            total_turns=len(self.turns),
            total_tokens=total_tokens,
            total_cost=total_cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            context_status=analysis.status,
            context_usage_percentage=analysis.usage_percentage,
            estimated_turns_remaining=max(0, estimated_remaining),
            warnings=analysis.warnings,
        )

    def can_add_turn(
        self,
        estimated_user_tokens: int,
        estimated_assistant_tokens: int,
    ) -> Dict[str, Any]:
        """
        Check if a new turn can be added without exceeding context.

        Args:
            estimated_user_tokens: Expected tokens in user message
            estimated_assistant_tokens: Expected tokens in assistant response

        Returns:
            Dictionary with feasibility analysis
        """
        # Get current token count
        current_analysis = self.context_analyzer.analyze_messages(
            self.messages,
            functions=self.functions if self.functions else None,
        )

        # Calculate tokens after adding turn
        tokens_after = current_analysis.total_tokens + estimated_user_tokens + estimated_assistant_tokens

        can_add = tokens_after <= self.model_config.max_input_tokens

        return {
            'can_add': can_add,
            'current_tokens': current_analysis.total_tokens,
            'tokens_after': tokens_after,
            'context_window': self.model_config.context_window,
            'max_input_tokens': self.model_config.max_input_tokens,
            'overflow': max(0, tokens_after - self.model_config.max_input_tokens),
            'recommendation': self._get_turn_recommendation(can_add, tokens_after, current_analysis.total_tokens),
        }

    def _get_turn_recommendation(
        self,
        can_add: bool,
        tokens_after: int,
        current_tokens: int,
    ) -> str:
        """Get recommendation for adding a turn."""
        if not can_add:
            return "❌ Cannot add turn - would exceed context window. Use summarize_conversation() first."

        usage_after = (tokens_after / self.model_config.context_window) * 100

        if usage_after >= 90:
            return "⚠️ Can add but context is critical (>90%). Consider summarizing soon."
        elif usage_after >= 70:
            return "⚠️ Can add but context is high (>70%). Monitor closely."
        else:
            return "✅ Safe to add turn."

    def summarize_conversation(
        self,
        keep_recent_turns: int = 5,
        summary_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Summarize conversation to reduce context usage.

        Args:
            keep_recent_turns: Number of recent turns to keep in full
            summary_template: Optional template for summary

        Returns:
            Dictionary with summarization results
        """
        if len(self.turns) <= keep_recent_turns:
            return {
                'summarized': False,
                'reason': 'Not enough turns to summarize',
                'total_turns': len(self.turns),
            }

        # Create summary of older turns
        older_turns = self.turns[:-keep_recent_turns]
        recent_turns = self.turns[-keep_recent_turns:]

        # Generate summary
        if summary_template:
            summary = summary_template
        else:
            summary = f"Previous conversation summary ({len(older_turns)} turns):\n"
            for i, turn in enumerate(older_turns, 1):
                summary += f"Turn {i}: User asked about something, assistant responded.\n"

        summary_tokens = self.token_counter.count_tokens(summary)

        # Calculate original tokens
        original_tokens = sum(turn.total_tokens for turn in older_turns)

        # Rebuild messages list
        new_messages = []

        # Keep system message
        for msg in self.messages:
            if msg.get('role') == MessageRole.SYSTEM.value:
                new_messages.append(msg)

        # Add summary
        new_messages.append({
            'role': MessageRole.SYSTEM.value,
            'content': summary,
        })

        # Add recent turns
        for turn in recent_turns:
            new_messages.append({
                'role': MessageRole.USER.value,
                'content': turn.user_message,
            })
            new_messages.append({
                'role': MessageRole.ASSISTANT.value,
                'content': turn.assistant_response,
            })

        # Update state
        old_message_count = len(self.messages)
        self.messages = new_messages

        return {
            'summarized': True,
            'original_turns': len(older_turns),
            'kept_turns': len(recent_turns),
            'original_tokens': original_tokens,
            'summary_tokens': summary_tokens,
            'tokens_saved': original_tokens - summary_tokens,
            'old_message_count': old_message_count,
            'new_message_count': len(self.messages),
        }

    def get_context_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed breakdown of context usage.

        Returns:
            Dictionary with context breakdown
        """
        analysis = self.context_analyzer.analyze_messages(
            self.messages,
            functions=self.functions if self.functions else None,
        )

        return {
            'total_tokens': analysis.total_tokens,
            'context_window': analysis.context_window,
            'usage_percentage': analysis.usage_percentage,
            'status': analysis.status.value,
            'breakdown': analysis.input_breakdown,
            'available_for_output': analysis.available_for_output,
            'warnings': analysis.warnings,
            'recommendations': analysis.recommendations,
        }

    def export_conversation(self) -> Dict[str, Any]:
        """
        Export conversation for analysis or storage.

        Returns:
            Dictionary with full conversation data
        """
        return {
            'model_name': self.model_name,
            'messages': self.messages,
            'turns': [
                {
                    'user_message': turn.user_message,
                    'assistant_response': turn.assistant_response,
                    'user_tokens': turn.user_tokens,
                    'assistant_tokens': turn.assistant_tokens,
                    'total_tokens': turn.total_tokens,
                    'cost': turn.cost,
                    'timestamp': turn.timestamp.isoformat(),
                    'metadata': turn.metadata,
                }
                for turn in self.turns
            ],
            'stats': self.get_stats().__dict__,
            'fixed_overhead': self.fixed_overhead,
        }
