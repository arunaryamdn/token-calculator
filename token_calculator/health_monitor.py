"""Context health monitoring and quality tracking."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .context_analyzer import ContextAnalyzer
from .conversation_manager import ConversationManager, Message


@dataclass
class HealthStatus:
    """Context health status for a conversation.

    Attributes:
        status: Overall health (healthy, context_rot, hallucination_risk, critical)
        context_usage: Percentage of context window used (0-100)
        rot_percentage: Percentage of context that appears irrelevant (0-100)
        quality_score: Overall quality score (0-100)
        warnings: List of warning messages
        recommendations: List of actionable recommendations
        metrics: Detailed health metrics
    """

    status: str
    context_usage: float
    rot_percentage: float
    quality_score: float
    warnings: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]

    def __str__(self) -> str:
        """String representation of health status."""
        status_emoji = {
            "healthy": "✅",
            "context_rot": "⚠️",
            "hallucination_risk": "🚨",
            "critical": "❌",
        }
        emoji = status_emoji.get(self.status, "❓")

        lines = [
            f"{emoji} Context Health: {self.status.upper()}",
            f"  Quality Score: {self.quality_score:.0f}/100",
            f"  Context Usage: {self.context_usage:.1f}%",
            f"  Rot: {self.rot_percentage:.1f}%",
        ]

        if self.warnings:
            lines.append("\n  Warnings:")
            for warning in self.warnings:
                lines.append(f"    ⚠️  {warning}")

        if self.recommendations:
            lines.append("\n  Recommendations:")
            for rec in self.recommendations:
                lines.append(f"    💡 {rec}")

        return "\n".join(lines)


@dataclass
class CompressionResult:
    """Result of context compression.

    Attributes:
        original_tokens: Original token count
        compressed_tokens: Compressed token count
        compression_ratio: Compression ratio (0-1, lower = more compression)
        messages: Compressed message list
        summary: Summary of what was compressed
        quality_impact: Estimated quality impact (0-1, 0 = no impact)
    """

    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    messages: List[Message]
    summary: str
    quality_impact: float

    def __str__(self) -> str:
        """String representation."""
        savings = self.original_tokens - self.compressed_tokens
        savings_pct = (savings / self.original_tokens * 100) if self.original_tokens > 0 else 0

        return (
            f"Compression Result:\n"
            f"  Original: {self.original_tokens:,} tokens\n"
            f"  Compressed: {self.compressed_tokens:,} tokens\n"
            f"  Savings: {savings:,} tokens ({savings_pct:.1f}%)\n"
            f"  Quality Impact: {self.quality_impact*100:.0f}%\n"
            f"  Summary: {self.summary}"
        )


class ConversationMonitor:
    """Monitor conversation context health and quality.

    Tracks conversation health over time, detects context rot,
    identifies hallucination risks, and provides intelligent
    compression strategies.

    Args:
        model: Model name
        agent_id: Optional agent identifier
        system_message: Optional system message

    Example:
        >>> from token_calculator import ConversationMonitor
        >>> monitor = ConversationMonitor(
        ...     model="gpt-4",
        ...     agent_id="customer-support"
        ... )
        >>> monitor.add_turn(user_msg, assistant_msg)
        >>> health = monitor.check_health()
        >>> if health.status == "context_rot":
        ...     compressed = monitor.compress_context(target_tokens=4000)
        ...     # Reset conversation with compressed context
    """

    def __init__(
        self,
        model: str,
        agent_id: Optional[str] = None,
        system_message: Optional[str] = None,
    ):
        """Initialize conversation monitor.

        Args:
            model: Model name
            agent_id: Optional agent identifier for tracking
            system_message: Optional system message
        """
        self.model = model
        self.agent_id = agent_id
        self.context_analyzer = ContextAnalyzer(model)
        self.conversation_manager = ConversationManager(
            model=model,
            system_message=system_message,
        )

        # Track conversation history
        self.messages: List[Message] = []
        if system_message:
            self.messages.append(
                Message(role="system", content=system_message, tokens=0)
            )

        # Track metrics over time
        self.turn_metrics: List[Dict[str, Any]] = []

    def add_turn(
        self,
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a conversation turn.

        Args:
            user_message: User message
            assistant_message: Assistant message
            metadata: Optional metadata for this turn

        Example:
            >>> monitor.add_turn(
            ...     user_message="What's the weather?",
            ...     assistant_message="I don't have access to weather data."
            ... )
        """
        # Add messages to conversation
        self.conversation_manager.add_turn(user_message, assistant_message)

        # Store messages
        from .tokenizer import count_tokens

        user_msg = Message(
            role="user",
            content=user_message,
            tokens=count_tokens(user_message, self.model),
        )
        assistant_msg = Message(
            role="assistant",
            content=assistant_message,
            tokens=count_tokens(assistant_message, self.model),
        )

        self.messages.append(user_msg)
        self.messages.append(assistant_msg)

        # Track metrics for this turn
        health = self.check_health()
        self.turn_metrics.append(
            {
                "turn": len(self.turn_metrics) + 1,
                "context_usage": health.context_usage,
                "quality_score": health.quality_score,
                "rot_percentage": health.rot_percentage,
                "metadata": metadata or {},
            }
        )

    def check_health(self) -> HealthStatus:
        """Check context health.

        Returns:
            HealthStatus with detailed health information

        Example:
            >>> health = monitor.check_health()
            >>> print(health.status)
            >>> if health.status != "healthy":
            ...     print(health.recommendations)
        """
        if not self.messages:
            return HealthStatus(
                status="healthy",
                context_usage=0,
                rot_percentage=0,
                quality_score=100,
                warnings=[],
                recommendations=[],
                metrics={},
            )

        # Analyze context
        analysis = self.context_analyzer.analyze_messages(
            [{"role": m.role, "content": m.content} for m in self.messages]
        )

        # Calculate metrics
        context_usage = analysis.usage_percentage
        rot_percentage = self._calculate_rot_percentage()
        quality_score = self._calculate_quality_score(analysis, rot_percentage)

        # Determine status
        status = self._determine_status(context_usage, rot_percentage, quality_score)

        # Generate warnings and recommendations
        warnings = self._generate_warnings(context_usage, rot_percentage, analysis)
        recommendations = self._generate_recommendations(
            status, context_usage, rot_percentage
        )

        return HealthStatus(
            status=status,
            context_usage=context_usage,
            rot_percentage=rot_percentage,
            quality_score=quality_score,
            warnings=warnings,
            recommendations=recommendations,
            metrics={
                "total_messages": len(self.messages),
                "total_tokens": analysis.total_tokens,
                "turns": len(self.turn_metrics),
                "context_status": analysis.status.value,
            },
        )

    def compress_context(
        self,
        strategy: str = "semantic",
        target_tokens: Optional[int] = None,
        keep_recent: int = 3,
    ) -> CompressionResult:
        """Compress context intelligently.

        Args:
            strategy: Compression strategy ("semantic", "simple", "aggressive")
            target_tokens: Target token count after compression
            keep_recent: Number of recent turns to always keep

        Returns:
            CompressionResult with compressed messages

        Example:
            >>> result = monitor.compress_context(
            ...     strategy="semantic",
            ...     target_tokens=4000,
            ...     keep_recent=3
            ... )
            >>> print(result)
            >>> # Update conversation with compressed context
            >>> compressed_messages = result.messages
        """
        if not self.messages:
            return CompressionResult(
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                messages=[],
                summary="No messages to compress",
                quality_impact=0,
            )

        from .tokenizer import count_tokens

        original_tokens = sum(m.tokens for m in self.messages)

        # Determine target if not specified
        if target_tokens is None:
            model_config = self.context_analyzer.model_config
            target_tokens = int(model_config.max_input_tokens * 0.6)  # 60% of max

        # Apply compression strategy
        if strategy == "simple":
            compressed = self._simple_compression(keep_recent)
            quality_impact = 0.2
        elif strategy == "semantic":
            compressed = self._semantic_compression(target_tokens, keep_recent)
            quality_impact = 0.1
        elif strategy == "aggressive":
            compressed = self._aggressive_compression(target_tokens, keep_recent)
            quality_impact = 0.3
        else:
            raise ValueError(f"Unknown compression strategy: {strategy}")

        compressed_tokens = sum(
            count_tokens(m.content, self.model) for m in compressed
        )

        # Generate summary
        removed = len(self.messages) - len(compressed)
        summary = f"Removed {removed} messages using {strategy} compression"

        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
            messages=compressed,
            summary=summary,
            quality_impact=quality_impact,
        )

    def _calculate_rot_percentage(self) -> float:
        """Calculate percentage of context that appears irrelevant.

        Uses heuristics:
        - Messages that are very old (>20 turns ago) have higher rot
        - Repeated assistant messages indicate confusion
        - Short messages have higher rot probability
        """
        if len(self.messages) <= 4:  # Too few messages to have rot
            return 0.0

        rot_score = 0.0
        total_tokens = sum(m.tokens for m in self.messages)

        if total_tokens == 0:
            return 0.0

        # Check for old messages
        conversation_turns = len([m for m in self.messages if m.role == "user"])
        for i, msg in enumerate(self.messages):
            msg_age = len(self.messages) - i

            # Old messages (>15 messages ago) likely less relevant
            if msg_age > 15:
                age_factor = min(1.0, (msg_age - 15) / 10)
                rot_score += msg.tokens * age_factor * 0.5

            # Very short assistant messages might be low value
            if msg.role == "assistant" and msg.tokens < 20:
                rot_score += msg.tokens * 0.3

        # Check for repetition (assistant repeating similar responses)
        assistant_messages = [m.content for m in self.messages if m.role == "assistant"]
        if len(assistant_messages) > 3:
            recent_msgs = assistant_messages[-3:]
            # Simple check: if messages are very similar length, might be repetitive
            avg_len = sum(len(m) for m in recent_msgs) / len(recent_msgs)
            if all(abs(len(m) - avg_len) < avg_len * 0.2 for m in recent_msgs):
                # Repetitive pattern detected
                rot_score += sum(
                    m.tokens for m in self.messages[-6:] if m.role == "assistant"
                ) * 0.4

        rot_percentage = (rot_score / total_tokens) * 100
        return min(100, rot_percentage)

    def _calculate_quality_score(
        self, analysis, rot_percentage: float
    ) -> float:
        """Calculate overall quality score (0-100)."""
        # Start at 100
        score = 100.0

        # Penalize high context usage
        if analysis.usage_percentage > 90:
            score -= (analysis.usage_percentage - 90) * 2  # Up to -20

        # Penalize context rot
        score -= rot_percentage * 0.5  # Up to -50

        # Penalize if conversation is very long
        if len(self.messages) > 50:
            score -= min(20, (len(self.messages) - 50) / 5)

        return max(0, score)

    def _determine_status(
        self,
        context_usage: float,
        rot_percentage: float,
        quality_score: float,
    ) -> str:
        """Determine overall health status."""
        # Critical: context overflow imminent
        if context_usage > 95 or quality_score < 30:
            return "critical"

        # Hallucination risk: high context usage
        if context_usage > 85:
            return "hallucination_risk"

        # Context rot: significant irrelevant context
        if rot_percentage > 40:
            return "context_rot"

        # Healthy
        return "healthy"

    def _generate_warnings(
        self,
        context_usage: float,
        rot_percentage: float,
        analysis,
    ) -> List[str]:
        """Generate warning messages."""
        warnings = []

        if context_usage > 90:
            warnings.append(
                f"Context window {context_usage:.1f}% full - overflow imminent"
            )

        if context_usage > 85:
            warnings.append(
                "High context usage may degrade response quality"
            )

        if rot_percentage > 40:
            warnings.append(
                f"{rot_percentage:.0f}% of context appears irrelevant - consider compression"
            )

        if len(self.messages) > 40:
            warnings.append(
                f"Long conversation ({len(self.messages)} messages) - quality may degrade"
            )

        # Check for assistant message repetition
        recent_assistant = [
            m for m in self.messages[-10:] if m.role == "assistant"
        ]
        if len(recent_assistant) > 3:
            avg_len = sum(m.tokens for m in recent_assistant) / len(recent_assistant)
            if all(abs(m.tokens - avg_len) < avg_len * 0.2 for m in recent_assistant):
                warnings.append(
                    "Detected repetitive responses - possible context confusion"
                )

        return warnings

    def _generate_recommendations(
        self,
        status: str,
        context_usage: float,
        rot_percentage: float,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if status == "critical":
            recommendations.append(
                "URGENT: Compress context or start new conversation immediately"
            )

        if status == "hallucination_risk":
            recommendations.append(
                "Context approaching limit - compress context to prevent quality degradation"
            )

        if rot_percentage > 40:
            recommendations.append(
                f"Use compress_context() to remove {rot_percentage:.0f}% irrelevant context"
            )

        if context_usage > 70 and status == "healthy":
            recommendations.append(
                "Proactively compress context to maintain quality"
            )

        if len(self.messages) > 30:
            recommendations.append(
                f"Consider conversation summarization - currently {len(self.messages)} messages"
            )

        if not recommendations:
            recommendations.append("Context health is good - no action needed")

        return recommendations

    def _simple_compression(self, keep_recent: int) -> List[Message]:
        """Simple compression: keep system message and recent N turns."""
        compressed = []

        # Keep system message
        system_msgs = [m for m in self.messages if m.role == "system"]
        compressed.extend(system_msgs)

        # Keep recent turns (user + assistant pairs)
        recent_messages = self.messages[-keep_recent * 2:]
        compressed.extend(recent_messages)

        return compressed

    def _semantic_compression(
        self,
        target_tokens: int,
        keep_recent: int,
    ) -> List[Message]:
        """Semantic compression: keep system, recent turns, and important messages."""
        compressed = []

        # Always keep system message
        system_msgs = [m for m in self.messages if m.role == "system"]
        compressed.extend(system_msgs)
        current_tokens = sum(m.tokens for m in compressed)

        # Always keep recent turns
        recent_messages = self.messages[-keep_recent * 2:]
        compressed.extend(recent_messages)
        current_tokens += sum(m.tokens for m in recent_messages)

        # Add important older messages until we hit target
        older_messages = [
            m for m in self.messages
            if m not in system_msgs and m not in recent_messages
        ]

        # Score messages by importance (longer messages = more important)
        scored_messages = [
            (m, m.tokens) for m in older_messages
        ]
        scored_messages.sort(key=lambda x: x[1], reverse=True)

        for msg, score in scored_messages:
            if current_tokens + msg.tokens <= target_tokens:
                compressed.insert(-len(recent_messages), msg)
                current_tokens += msg.tokens

        return compressed

    def _aggressive_compression(
        self,
        target_tokens: int,
        keep_recent: int,
    ) -> List[Message]:
        """Aggressive compression: minimal context, focus on recent."""
        compressed = []

        # Keep system message
        system_msgs = [m for m in self.messages if m.role == "system"]
        compressed.extend(system_msgs)

        # Only keep most recent turns
        keep_messages = min(keep_recent * 2, len(self.messages))
        recent = self.messages[-keep_messages:]
        compressed.extend(recent)

        return compressed
