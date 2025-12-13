# Know Your Tokens - Examples

This directory contains comprehensive examples demonstrating how to use the Know Your Tokens package.

## Examples

### 1. `basic_usage.py`
Basic token counting and analysis examples:
- Simple token counting
- Message token counting
- Comprehensive prompt analysis
- Listing available models

**Run it:**
```bash
python examples/basic_usage.py
```

### 2. `cost_analysis.py`
Cost calculation and comparison examples:
- Basic cost calculation
- Monthly cost estimation
- Comparing costs across models
- Calculating savings from optimization
- Finding affordable models

**Run it:**
```bash
python examples/cost_analysis.py
```

### 3. `conversation_management.py`
Managing multi-turn conversations:
- Basic conversation tracking
- RAG context integration
- Managing context limits
- Conversation summarization
- Exporting conversation data

**Run it:**
```bash
python examples/conversation_management.py
```

### 4. `optimization.py`
Token optimization strategies:
- Basic prompt optimization
- Aggressive optimization
- Getting optimization suggestions
- Comparing different phrasings
- Iterative optimization

**Run it:**
```bash
python examples/optimization.py
```

## Prerequisites

Make sure you have installed the package:
```bash
pip install -e .
```

Or with development dependencies:
```bash
pip install -e ".[dev]"
```

## Note

Some examples use OpenAI's tiktoken library for accurate token counting. If you encounter errors, install it:
```bash
pip install tiktoken
```

For other model providers, you may need additional libraries:
```bash
pip install transformers  # For Llama, Mistral, etc.
pip install anthropic     # For Claude models
```
