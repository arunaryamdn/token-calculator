"""
Token optimization utilities and strategies.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import re

from .tokenizer import TokenCounter
from .models import get_model_config


@dataclass
class OptimizationSuggestion:
    """A single optimization suggestion."""
    strategy: str
    description: str
    estimated_tokens_saved: int
    impact: str  # "low", "medium", "high"
    effort: str  # "easy", "moderate", "difficult"
    example: Optional[str] = None


@dataclass
class OptimizationResult:
    """Result of an optimization operation."""
    original_tokens: int
    optimized_tokens: int
    tokens_saved: int
    reduction_percentage: float
    optimized_text: str
    suggestions_applied: List[str]


class TokenOptimizer:
    """
    Optimize prompts and messages to reduce token usage.
    """

    def __init__(self, model_name: str):
        """
        Initialize optimizer for a specific model.

        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model_config = get_model_config(model_name)
        self.token_counter = TokenCounter(model_name)

    def analyze_text(self, text: str) -> List[OptimizationSuggestion]:
        """
        Analyze text and suggest optimizations.

        Args:
            text: Input text to analyze

        Returns:
            List of optimization suggestions
        """
        suggestions = []
        original_tokens = self.token_counter.count_tokens(text)

        # Check for excessive whitespace
        whitespace_suggestion = self._check_whitespace(text)
        if whitespace_suggestion:
            suggestions.append(whitespace_suggestion)

        # Check for repetitive content
        repetition_suggestion = self._check_repetition(text)
        if repetition_suggestion:
            suggestions.append(repetition_suggestion)

        # Check for verbose patterns
        verbosity_suggestions = self._check_verbosity(text)
        suggestions.extend(verbosity_suggestions)

        # Check for long examples
        example_suggestion = self._check_long_examples(text)
        if example_suggestion:
            suggestions.append(example_suggestion)

        # Check for formatting overhead
        formatting_suggestion = self._check_formatting(text)
        if formatting_suggestion:
            suggestions.append(formatting_suggestion)

        return suggestions

    def _check_whitespace(self, text: str) -> Optional[OptimizationSuggestion]:
        """Check for excessive whitespace."""
        # Count excessive newlines (more than 2 consecutive)
        excessive_newlines = len(re.findall(r'\n{3,}', text))

        if excessive_newlines > 0:
            original = self.token_counter.count_tokens(text)
            cleaned = re.sub(r'\n{3,}', '\n\n', text)
            cleaned = re.sub(r' {2,}', ' ', cleaned)
            optimized = self.token_counter.count_tokens(cleaned)

            if original - optimized > 5:
                return OptimizationSuggestion(
                    strategy="Remove excessive whitespace",
                    description="Text contains excessive whitespace (multiple newlines/spaces)",
                    estimated_tokens_saved=original - optimized,
                    impact="low",
                    effort="easy",
                    example="Replace multiple newlines with double newlines, multiple spaces with single spaces"
                )
        return None

    def _check_repetition(self, text: str) -> Optional[OptimizationSuggestion]:
        """Check for repetitive content."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Check for duplicate sentences
        unique_sentences = set(sentences)
        if len(sentences) - len(unique_sentences) > 2:
            duplicates = len(sentences) - len(unique_sentences)
            avg_sentence_tokens = self.token_counter.count_tokens(text) / len(sentences) if sentences else 0
            estimated_saved = int(duplicates * avg_sentence_tokens)

            return OptimizationSuggestion(
                strategy="Remove repetitive content",
                description=f"Found {duplicates} duplicate sentences",
                estimated_tokens_saved=estimated_saved,
                impact="medium",
                effort="moderate",
                example="Remove or consolidate repeated information"
            )
        return None

    def _check_verbosity(self, text: str) -> List[OptimizationSuggestion]:
        """Check for verbose patterns."""
        suggestions = []

        # Common verbose patterns
        verbose_patterns = {
            r'\bin order to\b': 'to',
            r'\bdue to the fact that\b': 'because',
            r'\bat this point in time\b': 'now',
            r'\bfor the purpose of\b': 'to',
            r'\bin the event that\b': 'if',
            r'\bit is important to note that\b': '',
            r'\bplease note that\b': '',
            r'\bas a matter of fact\b': 'actually',
        }

        total_saved = 0
        verbose_found = []

        for pattern, replacement in verbose_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                verbose_found.append(pattern.replace('\\b', ''))
                # Estimate tokens saved
                for match in matches:
                    original_tokens = self.token_counter.count_tokens(match)
                    replacement_tokens = self.token_counter.count_tokens(replacement) if replacement else 0
                    total_saved += original_tokens - replacement_tokens

        if verbose_found:
            suggestions.append(OptimizationSuggestion(
                strategy="Simplify verbose phrases",
                description=f"Found {len(verbose_found)} verbose patterns",
                estimated_tokens_saved=total_saved,
                impact="low",
                effort="easy",
                example=f"Examples: {', '.join(verbose_found[:3])}"
            ))

        return suggestions

    def _check_long_examples(self, text: str) -> Optional[OptimizationSuggestion]:
        """Check for excessively long examples."""
        # Look for code blocks or long quoted sections
        code_blocks = re.findall(r'```[\s\S]*?```', text)

        if code_blocks:
            total_code_tokens = sum(self.token_counter.count_tokens(block) for block in code_blocks)
            total_tokens = self.token_counter.count_tokens(text)

            # If code blocks consume >50% of tokens
            if total_code_tokens > total_tokens * 0.5:
                return OptimizationSuggestion(
                    strategy="Shorten examples",
                    description=f"Code examples use {total_code_tokens} tokens ({total_code_tokens/total_tokens*100:.1f}% of total)",
                    estimated_tokens_saved=int(total_code_tokens * 0.3),  # Estimate 30% reduction
                    impact="high",
                    effort="moderate",
                    example="Consider using shorter, focused examples or pseudocode"
                )
        return None

    def _check_formatting(self, text: str) -> Optional[OptimizationSuggestion]:
        """Check for formatting overhead."""
        # Count markdown formatting
        markdown_patterns = [
            r'\*\*[\s\S]*?\*\*',  # Bold
            r'\*[\s\S]*?\*',  # Italic
            r'#{1,6} ',  # Headers
            r'\[.*?\]\(.*?\)',  # Links
        ]

        formatting_chars = 0
        for pattern in markdown_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Count formatting characters (e.g., **, *, #, []())
                formatting_chars += len(match) - len(re.sub(r'[\*#\[\]\(\)]', '', match))

        if formatting_chars > 100:
            estimated_saved = formatting_chars // 4  # Rough estimate

            return OptimizationSuggestion(
                strategy="Reduce formatting overhead",
                description=f"Approximately {formatting_chars} characters used for markdown formatting",
                estimated_tokens_saved=estimated_saved,
                impact="low",
                effort="easy",
                example="Remove unnecessary bold/italic formatting"
            )
        return None

    def optimize_text(
        self,
        text: str,
        strategies: Optional[List[str]] = None,
        aggressive: bool = False,
    ) -> OptimizationResult:
        """
        Optimize text to reduce tokens.

        Args:
            text: Input text
            strategies: Specific strategies to apply (default: all)
            aggressive: Apply aggressive optimizations

        Returns:
            OptimizationResult with optimized text
        """
        original_tokens = self.token_counter.count_tokens(text)
        optimized = text
        applied_strategies = []

        # Apply optimizations
        if strategies is None or "whitespace" in strategies:
            optimized = self._optimize_whitespace(optimized)
            applied_strategies.append("whitespace")

        if strategies is None or "verbosity" in strategies:
            optimized = self._optimize_verbosity(optimized)
            applied_strategies.append("verbosity")

        if aggressive:
            if strategies is None or "aggressive_shortening" in strategies:
                optimized = self._aggressive_shorten(optimized)
                applied_strategies.append("aggressive_shortening")

        optimized_tokens = self.token_counter.count_tokens(optimized)
        tokens_saved = original_tokens - optimized_tokens
        reduction_pct = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0

        return OptimizationResult(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=tokens_saved,
            reduction_percentage=reduction_pct,
            optimized_text=optimized,
            suggestions_applied=applied_strategies,
        )

    def _optimize_whitespace(self, text: str) -> str:
        """Optimize whitespace."""
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        # Remove trailing whitespace
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        return text.strip()

    def _optimize_verbosity(self, text: str) -> str:
        """Optimize verbose patterns."""
        replacements = {
            r'\bin order to\b': 'to',
            r'\bdue to the fact that\b': 'because',
            r'\bat this point in time\b': 'now',
            r'\bfor the purpose of\b': 'to',
            r'\bin the event that\b': 'if',
            r'\bit is important to note that\b': '',
            r'\bplease note that\b': '',
            r'\bas a matter of fact\b': 'actually',
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _aggressive_shorten(self, text: str) -> str:
        """Apply aggressive shortening strategies."""
        # Remove filler words
        fillers = [
            r'\bvery\b', r'\breally\b', r'\bactually\b', r'\bbasically\b',
            r'\bliterally\b', r'\bjust\b', r'\bsimply\b'
        ]
        for filler in fillers:
            text = re.sub(filler, '', text, flags=re.IGNORECASE)

        # Clean up resulting double spaces
        text = re.sub(r' {2,}', ' ', text)

        return text

    def suggest_prompt_improvements(
        self,
        prompt: str,
        target_reduction: Optional[int] = None,
    ) -> List[OptimizationSuggestion]:
        """
        Suggest improvements for a prompt.

        Args:
            prompt: The prompt to analyze
            target_reduction: Target token reduction (optional)

        Returns:
            List of suggestions prioritized by impact
        """
        suggestions = self.analyze_text(prompt)

        # Add high-level suggestions
        tokens = self.token_counter.count_tokens(prompt)

        # Suggest splitting if very long
        if tokens > 2000:
            suggestions.append(OptimizationSuggestion(
                strategy="Split prompt",
                description=f"Prompt is very long ({tokens} tokens)",
                estimated_tokens_saved=0,
                impact="high",
                effort="moderate",
                example="Consider breaking into multiple focused prompts or using a multi-turn conversation"
            ))

        # Suggest using system message
        if "you are" in prompt.lower() and len(prompt) > 500:
            suggestions.append(OptimizationSuggestion(
                strategy="Use system message",
                description="Instructions could be moved to system message",
                estimated_tokens_saved=20,
                impact="low",
                effort="easy",
                example="Move role/behavior instructions to system message for better separation"
            ))

        # Sort by impact (high -> medium -> low)
        impact_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: (impact_order.get(x.impact, 3), -x.estimated_tokens_saved))

        return suggestions

    def compare_phrasings(
        self,
        phrasings: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Compare different phrasings to find the most token-efficient.

        Args:
            phrasings: List of alternative phrasings

        Returns:
            List of comparisons sorted by token count
        """
        comparisons = []

        for phrasing in phrasings:
            tokens = self.token_counter.count_tokens(phrasing)
            comparisons.append({
                'text': phrasing,
                'tokens': tokens,
                'characters': len(phrasing),
                'tokens_per_char': tokens / len(phrasing) if len(phrasing) > 0 else 0,
            })

        # Sort by token count
        comparisons.sort(key=lambda x: x['tokens'])

        return comparisons


def optimize_prompt(
    prompt: str,
    model_name: str,
    aggressive: bool = False,
) -> OptimizationResult:
    """
    Convenience function to optimize a prompt.

    Args:
        prompt: Input prompt
        model_name: Name of the model
        aggressive: Apply aggressive optimizations

    Returns:
        OptimizationResult
    """
    optimizer = TokenOptimizer(model_name)
    return optimizer.optimize_text(prompt, aggressive=aggressive)


def suggest_optimizations(
    text: str,
    model_name: str,
) -> List[OptimizationSuggestion]:
    """
    Convenience function to get optimization suggestions.

    Args:
        text: Input text
        model_name: Name of the model

    Returns:
        List of suggestions
    """
    optimizer = TokenOptimizer(model_name)
    return optimizer.suggest_prompt_improvements(text)
