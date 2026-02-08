# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-02-08

### Security Fixes
- **SQL Injection Prevention**: Added validation for filter keys and group_by dimensions in storage queries
- **SSRF Prevention**: Added webhook URL validation to block internal IPs, localhost, and metadata services
- **Connection Leak Prevention**: Implemented hybrid connection management (persistent for :memory:, context managers for files)
- **Input Validation**: Added text size limits (10MB) and structure validation to prevent DoS attacks
- **Thread Safety**: Added threading.Lock to BudgetTracker for concurrent access protection

### Added
- **Infrastructure Modules**:
  - `validation.py`: Centralized security validation with custom exceptions
  - `logging_config.py`: Structured logging configuration
  - `constants.py`: Extracted magic numbers and configuration constants
- **Security Documentation**: Added comprehensive SECURITY.md policy
- **CI/CD Pipeline**: Added GitHub Actions workflow for automated testing and quality checks
- **Comprehensive Test Suite**:
  - 36 security tests covering all vulnerabilities
  - 42 storage backend tests
  - Total 101+ tests with 49% code coverage (up from ~15%)

### Changed
- Replaced all `print()` statements with structured logging
- Added comprehensive type hints across modified modules
- Improved error handling with specific exception types
- Updated mypy configuration for stricter type checking
- Cleaned up repository (removed obsolete documentation and build artifacts)

### Fixed
- Race conditions in BudgetTracker with proper locking
- Connection leaks in SQLite storage operations
- Logging conflicts with reserved LogRecord fields

## [0.1.0] - 2025-12-13

### Added
- Initial release of Know Your Tokens
- Token counting for major LLM providers (OpenAI, Anthropic, Google, Meta, Mistral, Cohere)
- Context window analysis and management
- Cost calculation and comparison across models
- Conversation management with context tracking
- Token optimization utilities
- Support for 40+ LLM models
- Comprehensive examples and documentation
- Test suite with pytest

### Features
- **Token Counting**
  - Accurate tokenization for different models
  - Message-level token breakdown
  - Function/tool call token counting

- **Context Analysis**
  - Real-time context usage monitoring
  - Context break prediction
  - Maximum conversation turn estimation
  - Smart context splitting strategies

- **Cost Management**
  - Real-time cost tracking
  - Monthly/yearly cost projections
  - Cross-model cost comparison
  - Cost savings analysis

- **Conversation Management**
  - Multi-turn conversation tracking
  - Automatic summarization
  - Export functionality
  - RAG context support

- **Optimization**
  - Automatic prompt optimization
  - Verbose pattern detection
  - Phrasing comparison
  - Token reduction strategies

[0.1.0]: https://github.com/arunaryamdn/Know-your-tokens/releases/tag/v0.1.0
