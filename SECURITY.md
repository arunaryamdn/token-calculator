# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.2.x   | :white_check_mark: |
| 2.1.x   | :x:                |
| < 2.0   | :x:                |

## Security Features

Token-calculator v2.2.0 includes comprehensive security protections:

### SQL Injection Prevention

All user-provided identifiers (filter keys, group_by dimensions) are validated before SQL construction:

- ✅ Only alphanumeric characters, underscores, and hyphens allowed
- ✅ Maximum length enforced (256 characters)
- ✅ Parameterized queries for all values

**Safe Usage:**
```python
storage.query_events(filters={"agent_id": "my-agent"})  # ✅ Safe
storage.aggregate(metric="cost", group_by=["environment"])  # ✅ Safe
```

**Blocked:**
```python
storage.query_events(filters={"id'; DROP TABLE--": "value"})  # ❌ Raises ValidationError
```

### SSRF (Server-Side Request Forgery) Prevention

Webhook URLs are validated to prevent attacks against internal networks:

- ✅ HTTPS required by default
- ✅ Blocks localhost, 127.0.0.1
- ✅ Blocks private IP ranges (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
- ✅ Blocks cloud metadata services (169.254.169.254)
- ✅ 10-second request timeout

**Safe Usage:**
```python
AlertManager(webhook_url="https://hooks.slack.com/services/T00/B00/XXX")  # ✅ Safe
```

**Blocked:**
```python
AlertManager(webhook_url="http://localhost/evil")  # ❌ Raises SecurityError
AlertManager(webhook_url="https://192.168.1.1/internal")  # ❌ Raises SecurityError
```

**Development Override:**
For local testing, you can explicitly allow HTTP:
```python
from token_calculator.validation import validate_webhook_url

url = validate_webhook_url(
    "http://localhost:8080/webhook",
    allowed_schemes=["http", "https"]
)
```

### Input Validation & DoS Prevention

All text inputs are validated for size and structure:

- ✅ Maximum text size: 10MB (prevents DoS attacks)
- ✅ Message structure validation (role + content required)
- ✅ Model name validation (must exist in MODEL_DATABASE)
- ✅ Type checking (strings, lists, dicts as expected)

**Safe Usage:**
```python
count_tokens("Hello world", "gpt-4")  # ✅ Safe
count_messages([{"role": "user", "content": "Hi"}], "gpt-4")  # ✅ Safe
```

**Blocked:**
```python
count_tokens("x" * 20_000_000, "gpt-4")  # ❌ Raises ValidationError (>10MB)
count_messages([{"content": "Hi"}], "gpt-4")  # ❌ Raises ValidationError (missing role)
```

### Thread Safety

All storage operations are thread-safe:

- ✅ BudgetTracker uses `threading.Lock` for concurrent access
- ✅ SQLite connections properly managed (persistent for :memory:, context managers for files)
- ✅ No connection leaks even on errors

### Defense in Depth

Multiple security layers:

- ✅ URL validation on AlertManager initialization AND before sending
- ✅ SQL identifiers validated at query_events() AND aggregate()
- ✅ Proper exception handling with structured logging
- ✅ All connections closed via context managers

## Best Practices for Users

### 1. Validate User Input

If you accept user-provided filter keys or webhook URLs, validate them first:

```python
from token_calculator import ValidationError, SecurityError

try:
    storage.query_events(filters=user_provided_filters)
except ValidationError as e:
    # Handle invalid filter keys
    logger.error(f"Invalid filter: {e}")
```

### 2. Use HTTPS Webhooks

Always use HTTPS for production webhook URLs:

```python
# ✅ Production
AlertManager(webhook_url="https://hooks.example.com/webhook")

# ❌ Development only (explicitly opt-in)
from token_calculator.validation import validate_webhook_url
url = validate_webhook_url("http://localhost:8080", allowed_schemes=["http", "https"])
```

### 3. Set Resource Limits

For public-facing applications, consider additional rate limiting:

```python
# Track costs per user to prevent abuse
tracker.track_call(
    model="gpt-4",
    input_tokens=tokens,
    output_tokens=output,
    cost=cost,
    user_id=user_id  # Track per-user usage
)

# Check budget overages
if tracker.check_overage(f"user-{user_id}-budget"):
    raise Exception("User budget exceeded")
```

### 4. Enable Logging

Use structured logging to detect security issues:

```python
from token_calculator import configure_logging

configure_logging(level="INFO")  # Logs security events
```

### 5. Keep Dependencies Updated

```bash
pip install --upgrade token-calculator
```

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### DO NOT:
- ❌ Open a public GitHub issue
- ❌ Disclose the vulnerability publicly

### DO:
1. **Email**: Send details to [your-security-email@example.com]
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. **Response Time**: We will acknowledge within 48 hours
4. **Disclosure**: We will coordinate public disclosure after a fix is released

### What to Expect

1. **Acknowledgment**: Within 48 hours
2. **Assessment**: Within 7 days
3. **Fix**: Within 30 days for critical issues
4. **Release**: Security patch released as soon as possible
5. **Credit**: Public credit in release notes (if desired)

## Security Update Process

When we release security fixes:

1. **Security Advisory**: Published on GitHub
2. **Version Bump**: New version released to PyPI
3. **Changelog**: Security fixes documented
4. **Notification**: Users notified via GitHub releases

## Known Security Considerations

### 1. In-Memory Storage

`InMemoryStorage` keeps all data in RAM:
- ✅ Fast and convenient for development
- ⚠️ Data lost on process restart
- ⚠️ Not suitable for sensitive production data

**Recommendation**: Use `SQLiteStorage` or `PostgreSQLStorage` for production.

### 2. Webhook Security

Webhooks send data to external URLs:
- ✅ SSRF prevention included
- ⚠️ No webhook authentication/signing (you should validate on receiver side)
- ⚠️ Sensitive data may be transmitted

**Recommendation**: Use authenticated webhook endpoints and HTTPS only.

### 3. SQLite File Permissions

SQLite databases are files on disk:
- ⚠️ File permissions control access
- ⚠️ No built-in encryption

**Recommendation**: Set appropriate file permissions:
```bash
chmod 600 costs.db  # Owner read/write only
```

### 4. Sensitive Labels

Custom labels are stored in plaintext:
- ⚠️ Don't use PII (email, names, etc.) as label values
- ⚠️ Use IDs/hashes instead

**Example:**
```python
# ❌ Bad: Stores PII
tracker.track_call(model="gpt-4", ..., user_email="john@example.com")

# ✅ Good: Uses anonymized ID
tracker.track_call(model="gpt-4", ..., user_id="user-123")
```

## Security Checklist

Before deploying to production:

- [ ] Using HTTPS webhook URLs (if applicable)
- [ ] Validating user-provided filter keys
- [ ] Using persistent storage (SQLite/PostgreSQL, not InMemoryStorage)
- [ ] Setting appropriate file permissions on database files
- [ ] Not storing PII in labels or metadata
- [ ] Enabling structured logging
- [ ] Setting budget limits and alerts
- [ ] Keeping token-calculator updated

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [CWE-918: SSRF](https://cwe.mitre.org/data/definitions/918.html)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Questions?

For security questions, contact: [your-security-email@example.com]

For general questions, open a GitHub issue.
