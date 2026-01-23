# 🎯 Token Calculator

[![PyPI version](https://badge.fury.io/py/token-calculator.svg)](https://badge.fury.io/py/token-calculator)
[![Downloads](https://pepy.tech/badge/token-calculator)](https://pepy.tech/project/token-calculator)

**LLM Token Optimization and Cost Management for Developers**

Stop guessing about token usage and costs! TokenCost is a comprehensive Python package that helps developers understand, analyze, and optimize LLM token consumption across different models and providers.

## 🚀 Why Token Calculator?

In today's AI-driven world, developers face critical challenges:

- ❌ **Hidden Costs**: Many users don't realize the real cost of tokens until they receive huge bills
- ❌ **Context Confusion**: Unclear about context windows, max tokens, input vs output limits
- ❌ **Context Breaks**: Breaching context limits leads to reduced accuracy, context rot, and scope issues
- ❌ **Trial & Error**: No clear way to predict how many conversation turns are possible
- ❌ **Optimization Guesswork**: No systematic way to reduce token usage

**TokenCost solves all of these problems!**

## ✨ Features

### 🔢 Token Counting & Analysis
- Count tokens for any prompt or conversation
- Support for **major LLM providers**: OpenAI, Anthropic, Google, Meta, Mistral, Cohere
- Accurate tokenization using model-specific tokenizers
- Break down token usage by message role (system, user, assistant)

### 📊 Context Window Management
- Real-time context usage monitoring
- Identify when context will break **before** it happens
- Calculate maximum conversation turns with historical context, RAG, and tool calls
- Smart context splitting and summarization strategies

### 💰 Cost Calculation
- Real-time cost tracking for all major LLM models
- Compare costs across different models
- Monthly/yearly cost projections
- Cost-saving estimations from optimizations

### 💬 Conversation Management
- Track multi-turn conversations
- Automatic context monitoring
- Conversation summarization when approaching limits
- Export conversation data for analysis

### ⚡ Token Optimization
- Automatic detection of verbose patterns
- Prompt optimization suggestions
- Token reduction strategies
- Compare different phrasings for efficiency

## 📦 Installation

```bash
pip install token-calculator
```

For development:
```bash
pip install -e ".[dev]"
```

## 🎯 Quick Start

### Basic Token Counting

```python
from token_calculator import count_tokens, analyze_prompt

# Count tokens in a simple text
tokens = count_tokens("Hello, how are you?", model_name="gpt-4")
print(f"Tokens: {tokens}")

# Comprehensive analysis of a prompt
analysis = analyze_prompt(
    prompt="Write a detailed explanation of quantum computing",
    model_name="gpt-4",
    expected_output_tokens=500
)

print(f"Input tokens: {analysis['tokens']['input']}")
print(f"Total cost: {analysis['cost']['formatted']}")
print(f"Context usage: {analysis['context']['usage_percentage']:.1f}%")
print(f"Optimization suggestions: {analysis['optimization']['suggestions_count']}")
```

### Context Window Analysis

```python
from token_calculator import ContextAnalyzer

analyzer = ContextAnalyzer("gpt-4")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"},
    {"role": "assistant", "content": "Machine learning is..."},
]

analysis = analyzer.analyze_messages(messages)

print(f"Total tokens: {analysis.total_tokens}")
print(f"Usage: {analysis.usage_percentage:.1f}%")
print(f"Status: {analysis.status.value}")
print(f"Available for output: {analysis.available_for_output}")

# Get warnings
for warning in analysis.warnings:
    print(warning)

# Get recommendations
for rec in analysis.recommendations:
    print(rec)
```

### Cost Calculation

```python
from token_calculator import CostCalculator, compare_model_costs

# Calculate cost for a specific model
calculator = CostCalculator("gpt-4")
cost = calculator.calculate_cost(input_tokens=1000, output_tokens=500)

print(f"Input cost: ${cost.input_cost:.4f}")
print(f"Output cost: ${cost.output_cost:.4f}")
print(f"Total cost: ${cost.total_cost:.4f}")

# Estimate monthly costs
monthly = calculator.estimate_monthly_cost(
    requests_per_day=100,
    avg_input_tokens=500,
    avg_output_tokens=300
)

print(f"Monthly cost: ${monthly['monthly_cost']:.2f}")
print(f"Yearly cost: ${monthly['yearly_cost']:.2f}")

# Compare costs across models
comparisons = compare_model_costs(
    input_tokens=1000,
    output_tokens=500,
    model_names=["gpt-4", "gpt-4o-mini", "claude-3-5-sonnet-20241022"]
)

for comp in comparisons:
    print(f"{comp['model']}: ${comp['total_cost']:.4f}")
```

### Conversation Management

```python
from token_calculator import ConversationManager

# Initialize conversation
manager = ConversationManager(
    model_name="gpt-4",
    system_message="You are a helpful coding assistant.",
)

# Add conversation turns
manager.add_turn(
    user_message="How do I optimize Python code?",
    assistant_response="Here are some ways to optimize Python code..."
)

manager.add_turn(
    user_message="What about async programming?",
    assistant_response="Async programming in Python..."
)

# Get statistics
stats = manager.get_stats()
print(f"Total turns: {stats.total_turns}")
print(f"Total cost: ${stats.total_cost:.4f}")
print(f"Context usage: {stats.context_usage_percentage:.1f}%")
print(f"Estimated remaining turns: {stats.estimated_turns_remaining}")

# Check if we can add more turns
can_add = manager.can_add_turn(
    estimated_user_tokens=50,
    estimated_assistant_tokens=200
)
print(can_add['recommendation'])

# Summarize when needed
if stats.context_usage_percentage > 70:
    result = manager.summarize_conversation(keep_recent_turns=3)
    print(f"Saved {result['tokens_saved']} tokens through summarization")
```

### Token Optimization

```python
from token_calculator import TokenOptimizer, optimize_prompt

# Optimize a prompt
optimizer = TokenOptimizer("gpt-4")

prompt = """
In order to complete this task, it is important to note that
you should be very careful and really think about the best
approach for the purpose of achieving optimal results.
"""

# Get optimization suggestions
suggestions = optimizer.suggest_prompt_improvements(prompt)
for suggestion in suggestions:
    print(f"💡 {suggestion.strategy}")
    print(f"   {suggestion.description}")
    print(f"   Potential savings: {suggestion.estimated_tokens_saved} tokens")
    print(f"   Impact: {suggestion.impact} | Effort: {suggestion.effort}")

# Apply optimizations
result = optimizer.optimize_text(prompt, aggressive=True)
print(f"\nOriginal: {result.original_tokens} tokens")
print(f"Optimized: {result.optimized_tokens} tokens")
print(f"Saved: {result.tokens_saved} tokens ({result.reduction_percentage:.1f}%)")
print(f"\nOptimized text:\n{result.optimized_text}")
```

### Model Search & Comparison

```python
from token_calculator import search_models, list_models, ModelProvider

# List all models from a provider
openai_models = list_models(provider=ModelProvider.OPENAI)
print(f"OpenAI models: {openai_models}")

# Search for models meeting specific criteria
affordable_models = search_models(
    min_context=32000,
    max_cost_per_1k_input=0.001,
    supports_function_calling=True
)

print("Affordable models with 32k+ context and function calling:")
for model in affordable_models:
    print(f"  - {model}")
```

## 📚 Advanced Usage

### Estimating Maximum Conversation Turns

```python
from token_calculator import ContextAnalyzer

analyzer = ContextAnalyzer("gpt-4")

# Estimate max turns with RAG and function calling
estimate = analyzer.estimate_max_turns(
    avg_user_tokens=100,
    avg_assistant_tokens=300,
    system_tokens=50,
    rag_tokens=2000,  # RAG context
    function_tokens=500  # Function definitions
)

print(f"Maximum conversation turns: {estimate['max_turns']}")
print(f"Warning at turn: {estimate['warning_at_turn']}")
print(f"Critical at turn: {estimate['critical_at_turn']}")
```

### Cost Savings Analysis

```python
from token_calculator import CostCalculator

calculator = CostCalculator("gpt-4")

savings = calculator.estimate_cost_savings(
    current_tokens=1000,
    optimized_tokens=700,
    requests_per_month=10000,
    token_type="input"
)

print(f"Tokens saved per request: {savings['tokens_saved_per_request']}")
print(f"Reduction: {savings['reduction_percentage']:.1f}%")
print(f"Monthly savings: ${savings['monthly_savings']:.2f}")
print(f"Yearly savings: ${savings['yearly_savings']:.2f}")
```

### Comparing Different Phrasings

```python
from token_calculator import TokenOptimizer

optimizer = TokenOptimizer("gpt-4")

phrasings = [
    "Please explain how this works",
    "Explain how this works",
    "How does this work?",
    "How this works",
]

comparisons = optimizer.compare_phrasings(phrasings)

for comp in comparisons:
    print(f"{comp['tokens']} tokens: {comp['text']}")
```

## 🎓 Use Cases

### 1. Development & Debugging
- Understand token usage during development
- Identify expensive prompts before production
- Optimize prompts systematically

### 2. Production Monitoring
- Track token usage in real-time
- Set up alerts for high context usage
- Monitor costs across different features

### 3. Cost Optimization
- Identify cost-saving opportunities
- Compare model alternatives
- Optimize without sacrificing quality

### 4. RAG Applications
- Calculate token budget for context
- Balance between context and generation
- Optimize document chunking

### 5. Agent Systems
- Track tool call overhead
- Manage multi-turn agent conversations
- Prevent context overflow in loops

## 🔧 Supported Models

### OpenAI
- GPT-4, GPT-4-32K, GPT-4-Turbo, GPT-4o, GPT-4o-mini
- GPT-3.5-Turbo, GPT-3.5-Turbo-16K

### Anthropic
- Claude Opus 4.5, Claude 3 Opus, Claude 3.5 Sonnet, Claude 3 Sonnet
- Claude 3 Haiku, Claude 3.5 Haiku

### Google
- Gemini Pro, Gemini 1.5 Pro, Gemini 1.5 Flash

### Meta
- Llama 2 (7B, 13B, 70B)
- Llama 3 (8B, 70B)
- Llama 3.1 (8B, 70B, 405B)

### Mistral
- Mistral 7B, Mistral 8x7B
- Mistral Small, Medium, Large

### Cohere
- Command, Command Light
- Command R, Command R Plus

*More models added regularly!*

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built to make LLM development easier and more cost-effective for everyone.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/arunaryamdn/Know-your-tokens/issues)
- **Discussions**: [GitHub Discussions](https://github.com/arunaryamdn/Know-your-tokens/discussions)

---

**Made with ❤️ for the LLM developer community**
