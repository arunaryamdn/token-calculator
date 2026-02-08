"""
Constants and configuration values for token-calculator.

This module centralizes magic numbers and configuration values that were
previously hardcoded throughout the codebase. This improves maintainability
and makes it easier to adjust thresholds and limits.

Usage:
    from token_calculator.constants import (
        CONTEXT_ROT_THRESHOLD_PCT,
        MAX_TEXT_LENGTH,
    )
"""

# ============================================================================
# Context Health & Monitoring Thresholds
# ============================================================================

# Context rot detection thresholds (percentages)
# Context rot threshold percentage. Above this, context is degraded.
CONTEXT_ROT_THRESHOLD_PCT = 40.0

# Context usage warning threshold. Above this, approaching limits.
CONTEXT_USAGE_WARNING_PCT = 85.0

# Context usage critical threshold. Above this, risk of exceeding limits.
CONTEXT_USAGE_CRITICAL_PCT = 95.0

# Minimum acceptable quality score. Below this, context quality is poor.
QUALITY_SCORE_CRITICAL = 30.0

# ============================================================================
# Message Analysis & Context Rot
# ============================================================================

# Message age thresholds (for rot calculation)
# Number of messages before a message is considered 'old' for rot calculation
OLD_MESSAGE_THRESHOLD = 15

# Divisor for calculating age factor in rot score
AGE_FACTOR_DIVISOR = 10

# Multiplier for age factor when calculating rot contribution
AGE_MULTIPLIER = 0.5

# Message characteristics
# Minimum number of messages required before rot detection is meaningful
MIN_MESSAGES_FOR_ROT = 4

# Token count threshold. Messages with fewer tokens are considered 'short'
SHORT_MESSAGE_TOKENS = 20

# Number of recent messages to check for repetitive content
REPETITION_WINDOW = 5

# Similarity threshold (0-1) for detecting repetitive messages
REPETITION_THRESHOLD = 0.7

# ============================================================================
# Compression & Optimization
# ============================================================================

# Default target percentage for context compression (60% of original)
DEFAULT_COMPRESSION_TARGET_PCT = 0.6

# Default number of recent conversation turns to preserve during compression
DEFAULT_KEEP_RECENT_TURNS = 3

# Minimum messages required before compression is beneficial
COMPRESSION_MIN_MESSAGES = 5

# ============================================================================
# Input Validation & Security Limits
# ============================================================================

# Maximum text length in characters (10 MB). Prevents DoS attacks.
MAX_TEXT_LENGTH = 10_000_000

# Maximum length for SQL identifiers (label keys, dimension names)
MAX_IDENTIFIER_LENGTH = 256

# Maximum timeout in seconds for webhook HTTP requests
MAX_WEBHOOK_TIMEOUT = 10

# Maximum token count per field. Sanity check for unrealistic values.
MAX_TOKEN_COUNT = 1_000_000

# ============================================================================
# Storage & Query Defaults
# ============================================================================

# Default limit for query results when no limit is specified
DEFAULT_QUERY_LIMIT = 1000

# Default number of days to retain tracking events
DEFAULT_RETENTION_DAYS = 90

# ============================================================================
# Cost & Budget Thresholds
# ============================================================================

# Minimum samples required for meaningful anomaly detection
ANOMALY_DETECTION_MIN_SAMPLES = 10

# Number of days to use for baseline cost calculation
ANOMALY_DETECTION_BASELINE_DAYS = 7

# Multiplier for detecting anomalies (cost > baseline * multiplier)
ANOMALY_THRESHOLD_MULTIPLIER = 3.0

# ============================================================================
# Forecasting & Prediction
# ============================================================================

# Minimum days of historical data required for forecasting
FORECAST_MIN_HISTORICAL_DAYS = 7

# Default number of days to forecast into the future
FORECAST_DEFAULT_HORIZON_DAYS = 30

# Confidence level for prediction intervals (95%)
FORECAST_CONFIDENCE_LEVEL = 0.95

# ============================================================================
# Alert System
# ============================================================================

# Default cooldown period between repeated alerts (1 hour)
ALERT_DEFAULT_COOLDOWN_MINUTES = 60

# Maximum number of alerts to keep in history
ALERT_HISTORY_MAX_SIZE = 1000

# ============================================================================
# Model Selection & A/B Testing
# ============================================================================

# Minimum samples per variant for meaningful A/B test results
AB_TEST_MIN_SAMPLES = 30

# Confidence level for A/B test statistical significance
AB_TEST_CONFIDENCE_LEVEL = 0.95

# ============================================================================
# Performance & Optimization
# ============================================================================

# Batch size for bulk database inserts
BATCH_INSERT_SIZE = 100

# Default connection pool size for database backends
CONNECTION_POOL_SIZE = 5

# Default TTL for cached results (5 minutes)
CACHE_TTL_SECONDS = 300

# ============================================================================
# Workflow Tracking
# ============================================================================

# Threshold for detecting parallel agent execution (overlap > 30%)
WORKFLOW_PARALLEL_THRESHOLD = 0.3

# Efficiency score below this triggers warning (60%)
WORKFLOW_EFFICIENCY_WARNING = 0.6

# Percentage of total time spent by an agent to be considered a bottleneck
BOTTLENECK_THRESHOLD_PCT = 40.0

# ============================================================================
# Token Counting & Approximation
# ============================================================================

# Approximate characters per token when exact counting unavailable
TOKEN_APPROXIMATION_CHARS_PER_TOKEN = 4

# Overhead tokens per function call in message
FUNCTION_CALL_OVERHEAD_TOKENS = 7

# Base overhead tokens per message
MESSAGE_OVERHEAD_TOKENS = 3

# ============================================================================
# Logging & Debugging
# ============================================================================

# Default logging level for the package
LOG_LEVEL_DEFAULT = "INFO"

# Timestamp format for log messages
LOG_FORMAT_TIMESTAMP = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# API Rate Limits (for external services)
# ============================================================================

# Default rate limit for external API calls
RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# Window size for rate limiting (60 seconds)
RATE_LIMIT_WINDOW_SECONDS = 60

# ============================================================================
# Feature Flags
# ============================================================================

# Whether to enable telemetry/analytics (disabled by default)
ENABLE_TELEMETRY = False

# Whether to enable caching for expensive operations
ENABLE_CACHING = True

# Whether to enable strict validation (v2.2: False, v3.0: True)
STRICT_VALIDATION = False
