# Contributing to Know Your Tokens

Thank you for your interest in contributing to Know Your Tokens! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Know-your-tokens.git
   cd Know-your-tokens
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   black know_your_tokens tests examples
   isort know_your_tokens tests examples
   ```

5. Run linters:
   ```bash
   flake8 know_your_tokens tests
   mypy know_your_tokens
   ```

6. Commit your changes:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

8. Create a Pull Request

## Adding New Models

To add support for a new LLM model:

1. Add the model configuration to `know_your_tokens/models.py` in the `MODEL_DATABASE` dictionary
2. Include:
   - Model name
   - Provider
   - Context window size
   - Max output tokens
   - Pricing (cost per 1k input/output tokens)
   - Tokenizer name
   - Feature support (function calling, vision, etc.)

3. Add tests for the new model in `tests/test_models.py`

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Add comments for complex logic

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases
- Use pytest fixtures for common setup

## Documentation

- Update README.md if adding new features
- Add examples to the `examples/` directory
- Update docstrings
- Add comments for complex code

## Pull Request Guidelines

- One feature per pull request
- Clear description of changes
- Reference related issues
- Ensure all tests pass
- Update documentation
- Follow the existing code style

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about usage
- Documentation improvements

Thank you for contributing!
