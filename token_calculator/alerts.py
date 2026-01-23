"""Alerting and notification system for LLM usage monitoring."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .storage import TrackingEvent


@dataclass
class Alert:
    """Alert triggered by a rule.

    Attributes:
        rule_name: Name of the rule that triggered
        severity: Alert severity (info, warning, critical)
        message: Alert message
        timestamp: When alert was triggered
        event: Event that triggered the alert
        metadata: Additional metadata
    """

    rule_name: str
    severity: str
    message: str
    timestamp: datetime
    event: Optional[TrackingEvent]
    metadata: Dict[str, Any]

    def __str__(self) -> str:
        """String representation."""
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
        }
        emoji = severity_emoji.get(self.severity, "❓")

        return (
            f"{emoji} [{self.severity.upper()}] {self.rule_name}\n"
            f"   {self.message}\n"
            f"   Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )


@dataclass
class AlertRule:
    """Alert rule configuration.

    Attributes:
        name: Rule name
        condition: Condition function that returns True to trigger alert
        severity: Alert severity (info, warning, critical)
        message_template: Message template (can use {field} placeholders)
        channels: Notification channels (console, webhook, email)
        cooldown_minutes: Minutes between alerts for same rule
        enabled: Whether rule is enabled
    """

    name: str
    condition: Callable[[TrackingEvent], bool]
    severity: str
    message_template: str
    channels: List[str]
    cooldown_minutes: int = 60
    enabled: bool = True


class AlertManager:
    """Manage alerts and notifications.

    Monitors events and triggers alerts based on configured rules.
    Supports multiple notification channels and alert cooldowns.

    Example:
        >>> from token_calculator import AlertManager
        >>> alerts = AlertManager()
        >>> # Add cost threshold alert
        >>> alerts.add_rule(AlertRule(
        ...     name="high-cost-call",
        ...     condition=lambda e: e.cost > 1.0,
        ...     severity="warning",
        ...     message_template="High cost call: ${cost:.2f}",
        ...     channels=["console"]
        ... ))
        >>> # Check event
        >>> triggered = alerts.check_event(event)
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize alert manager.

        Args:
            webhook_url: Optional webhook URL for notifications
        """
        self.rules: List[AlertRule] = []
        self.webhook_url = webhook_url
        self.alert_history: List[Alert] = []
        self.last_alert_time: Dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule):
        """Add an alert rule.

        Args:
            rule: Alert rule to add

        Example:
            >>> alerts.add_rule(AlertRule(
            ...     name="budget-exceeded",
            ...     condition=lambda e: total_cost > budget,
            ...     severity="critical",
            ...     message_template="Budget exceeded!",
            ...     channels=["console", "webhook"]
            ... ))
        """
        self.rules.append(rule)

    def check_event(self, event: TrackingEvent) -> List[Alert]:
        """Check if event triggers any alerts.

        Args:
            event: Event to check

        Returns:
            List of triggered alerts

        Example:
            >>> triggered = alerts.check_event(event)
            >>> for alert in triggered:
            ...     print(alert)
        """
        triggered = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.name in self.last_alert_time:
                last_time = self.last_alert_time[rule.name]
                cooldown_end = last_time + timedelta(minutes=rule.cooldown_minutes)
                if datetime.now() < cooldown_end:
                    continue  # Still in cooldown

            # Check condition
            try:
                if rule.condition(event):
                    # Trigger alert
                    message = self._format_message(rule.message_template, event)

                    alert = Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=message,
                        timestamp=datetime.now(),
                        event=event,
                        metadata={},
                    )

                    # Send notifications
                    self._send_notifications(alert, rule.channels)

                    # Record alert
                    triggered.append(alert)
                    self.alert_history.append(alert)
                    self.last_alert_time[rule.name] = datetime.now()

            except Exception as e:
                # Don't let alert failures break the system
                print(f"Error checking rule {rule.name}: {e}")

        return triggered

    def add_budget_alert(
        self,
        budget_amount: float,
        threshold_pct: float = 0.8,
        severity: str = "warning",
    ):
        """Add a budget threshold alert.

        Args:
            budget_amount: Budget amount
            threshold_pct: Percentage of budget to trigger at (0.8 = 80%)
            severity: Alert severity

        Example:
            >>> alerts.add_budget_alert(
            ...     budget_amount=1000,
            ...     threshold_pct=0.8,
            ...     severity="warning"
            ... )
        """
        # This is a simplified version - in practice would track cumulative cost
        threshold = budget_amount * threshold_pct

        self.add_rule(
            AlertRule(
                name=f"budget-{threshold_pct*100:.0f}pct",
                condition=lambda e: False,  # Placeholder - need cumulative tracking
                severity=severity,
                message_template=f"Budget {threshold_pct*100:.0f}% reached",
                channels=["console"],
            )
        )

    def add_cost_spike_alert(
        self,
        threshold_multiplier: float = 2.0,
        severity: str = "warning",
    ):
        """Add a cost spike alert.

        Args:
            threshold_multiplier: Multiplier vs baseline (2.0 = 200% of normal)
            severity: Alert severity

        Example:
            >>> alerts.add_cost_spike_alert(
            ...     threshold_multiplier=2.0,
            ...     severity="warning"
            ... )
        """
        self.add_rule(
            AlertRule(
                name="cost-spike",
                condition=lambda e: e.cost > 0.5,  # Simple threshold
                severity=severity,
                message_template="Cost spike detected: ${cost:.2f}",
                channels=["console"],
            )
        )

    def add_context_overflow_alert(self, model: str):
        """Add a context overflow alert.

        Args:
            model: Model to monitor

        Example:
            >>> alerts.add_context_overflow_alert("gpt-4")
        """
        from .models import get_model_config

        config = get_model_config(model)
        threshold = config.max_input_tokens * 0.9

        self.add_rule(
            AlertRule(
                name="context-overflow-warning",
                condition=lambda e: (
                    e.input_tokens + e.output_tokens > threshold
                ),
                severity="warning",
                message_template=(
                    "Context approaching limit: {input_tokens} + {output_tokens} tokens"
                ),
                channels=["console"],
            )
        )

    def get_recent_alerts(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
    ) -> List[Alert]:
        """Get recent alerts.

        Args:
            hours: Hours to look back
            severity: Optional severity filter

        Returns:
            List of recent alerts

        Example:
            >>> recent = alerts.get_recent_alerts(hours=24, severity="critical")
            >>> print(f"Critical alerts: {len(recent)}")
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        filtered = [
            a for a in self.alert_history
            if a.timestamp > cutoff
        ]

        if severity:
            filtered = [a for a in filtered if a.severity == severity]

        return filtered

    def _format_message(self, template: str, event: TrackingEvent) -> str:
        """Format alert message with event data."""
        try:
            return template.format(
                cost=event.cost,
                input_tokens=event.input_tokens,
                output_tokens=event.output_tokens,
                model=event.model,
                **event.labels,
            )
        except KeyError:
            return template  # Return template as-is if formatting fails

    def _send_notifications(self, alert: Alert, channels: List[str]):
        """Send alert notifications to channels."""
        for channel in channels:
            if channel == "console":
                print(alert)

            elif channel == "webhook" and self.webhook_url:
                self._send_webhook(alert)

            elif channel == "email":
                # Email not implemented - would need SMTP configuration
                pass

    def _send_webhook(self, alert: Alert):
        """Send webhook notification."""
        try:
            import urllib.request

            payload = {
                "text": str(alert),
                "severity": alert.severity,
                "rule": alert.rule_name,
                "timestamp": alert.timestamp.isoformat(),
            }

            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            urllib.request.urlopen(req)

        except Exception as e:
            print(f"Failed to send webhook: {e}")
