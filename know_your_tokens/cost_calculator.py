"""
Cost calculation utilities for LLM token usage.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import get_model_config
from .tokenizer import TokenCounter


@dataclass
class CostBreakdown:
    """Breakdown of LLM usage costs."""
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model_name: str
    timestamp: datetime
    details: Dict[str, Any]


class CostCalculator:
    """
    Calculate costs for LLM token usage.
    """

    def __init__(self, model_name: str):
        """
        Initialize cost calculator for a specific model.

        Args:
            model_name: Name of the model
        """
        self.model_name = model_name
        self.model_config = get_model_config(model_name)
        self.token_counter = TokenCounter(model_name)

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> CostBreakdown:
        """
        Calculate cost for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            CostBreakdown with detailed cost information
        """
        # Calculate costs
        input_cost = (input_tokens / 1000) * self.model_config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.model_config.cost_per_1k_output
        total_cost = input_cost + output_cost

        return CostBreakdown(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_name=self.model_name,
            timestamp=datetime.now(),
            details={
                'cost_per_1k_input': self.model_config.cost_per_1k_input,
                'cost_per_1k_output': self.model_config.cost_per_1k_output,
            }
        )

    def calculate_message_cost(
        self,
        messages: List[Dict[str, Any]],
        estimated_output_tokens: int,
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> CostBreakdown:
        """
        Calculate cost for a conversation.

        Args:
            messages: List of message dictionaries
            estimated_output_tokens: Expected tokens in response
            functions: Optional function definitions

        Returns:
            CostBreakdown with cost details
        """
        # Count input tokens
        token_breakdown = self.token_counter.count_messages(messages, include_function_tokens=True)
        input_tokens = token_breakdown['total']

        # Add function definition tokens
        if functions:
            input_tokens += self.token_counter.count_function_definitions(functions)

        # Calculate cost
        return self.calculate_cost(input_tokens, estimated_output_tokens)

    def estimate_monthly_cost(
        self,
        requests_per_day: int,
        avg_input_tokens: int,
        avg_output_tokens: int,
    ) -> Dict[str, Any]:
        """
        Estimate monthly costs based on usage patterns.

        Args:
            requests_per_day: Average API requests per day
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request

        Returns:
            Dictionary with cost projections
        """
        # Calculate daily costs
        cost_per_request = self.calculate_cost(avg_input_tokens, avg_output_tokens)
        daily_cost = cost_per_request.total_cost * requests_per_day

        # Project to different time periods
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30
        yearly_cost = daily_cost * 365

        return {
            'cost_per_request': cost_per_request.total_cost,
            'daily_cost': daily_cost,
            'weekly_cost': weekly_cost,
            'monthly_cost': monthly_cost,
            'yearly_cost': yearly_cost,
            'daily_requests': requests_per_day,
            'monthly_requests': requests_per_day * 30,
            'yearly_requests': requests_per_day * 365,
            'breakdown': {
                'input_tokens_per_request': avg_input_tokens,
                'output_tokens_per_request': avg_output_tokens,
                'input_cost_per_request': cost_per_request.input_cost,
                'output_cost_per_request': cost_per_request.output_cost,
            },
            'warnings': self._generate_cost_warnings(monthly_cost, yearly_cost),
        }

    def _generate_cost_warnings(self, monthly_cost: float, yearly_cost: float) -> List[str]:
        """Generate cost warnings based on projections."""
        warnings = []

        if monthly_cost > 1000:
            warnings.append(
                f"💰 High monthly cost projected: ${monthly_cost:.2f}/month. "
                "Consider optimization strategies."
            )

        if yearly_cost > 10000:
            warnings.append(
                f"💰 Very high yearly cost projected: ${yearly_cost:.2f}/year. "
                "Strongly recommend cost optimization."
            )

        return warnings

    def compare_models(
        self,
        input_tokens: int,
        output_tokens: int,
        model_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compare costs across different models.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_names: List of models to compare (default: all models)

        Returns:
            List of cost comparisons, sorted by total cost
        """
        from .models import MODEL_DATABASE

        if model_names is None:
            model_names = list(MODEL_DATABASE.keys())

        comparisons = []

        for model_name in model_names:
            try:
                calculator = CostCalculator(model_name)
                cost = calculator.calculate_cost(input_tokens, output_tokens)

                model_config = get_model_config(model_name)

                comparisons.append({
                    'model': model_name,
                    'provider': model_config.provider.value,
                    'total_cost': cost.total_cost,
                    'input_cost': cost.input_cost,
                    'output_cost': cost.output_cost,
                    'context_window': model_config.context_window,
                    'supports_functions': model_config.supports_function_calling,
                    'supports_vision': model_config.supports_vision,
                })
            except Exception:
                # Skip models that fail
                continue

        # Sort by total cost
        comparisons.sort(key=lambda x: x['total_cost'])

        return comparisons

    def calculate_batch_cost(
        self,
        batch_requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate cost for a batch of requests.

        Args:
            batch_requests: List of requests, each with 'input_tokens' and 'output_tokens'

        Returns:
            Dictionary with batch cost analysis
        """
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        request_costs = []

        for req in batch_requests:
            input_tokens = req.get('input_tokens', 0)
            output_tokens = req.get('output_tokens', 0)

            cost = self.calculate_cost(input_tokens, output_tokens)

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_cost += cost.total_cost

            request_costs.append({
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': cost.total_cost,
            })

        return {
            'total_requests': len(batch_requests),
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_cost': total_cost,
            'average_cost_per_request': total_cost / len(batch_requests) if batch_requests else 0,
            'request_costs': request_costs,
        }

    def estimate_cost_savings(
        self,
        current_tokens: int,
        optimized_tokens: int,
        requests_per_month: int,
        token_type: str = "input",
    ) -> Dict[str, Any]:
        """
        Estimate cost savings from token optimization.

        Args:
            current_tokens: Current token usage
            optimized_tokens: Optimized token usage
            requests_per_month: Number of requests per month
            token_type: Either "input" or "output"

        Returns:
            Dictionary with savings analysis
        """
        tokens_saved = current_tokens - optimized_tokens
        reduction_percentage = (tokens_saved / current_tokens * 100) if current_tokens > 0 else 0

        # Calculate costs
        if token_type == "input":
            cost_per_1k = self.model_config.cost_per_1k_input
        else:
            cost_per_1k = self.model_config.cost_per_1k_output

        current_cost_per_request = (current_tokens / 1000) * cost_per_1k
        optimized_cost_per_request = (optimized_tokens / 1000) * cost_per_1k
        savings_per_request = current_cost_per_request - optimized_cost_per_request

        monthly_savings = savings_per_request * requests_per_month
        yearly_savings = monthly_savings * 12

        return {
            'tokens_saved_per_request': tokens_saved,
            'reduction_percentage': reduction_percentage,
            'current_cost_per_request': current_cost_per_request,
            'optimized_cost_per_request': optimized_cost_per_request,
            'savings_per_request': savings_per_request,
            'monthly_savings': monthly_savings,
            'yearly_savings': yearly_savings,
            'monthly_requests': requests_per_month,
        }


def calculate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> CostBreakdown:
    """
    Convenience function to calculate cost.

    Args:
        model_name: Name of the model
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        CostBreakdown with cost details
    """
    calculator = CostCalculator(model_name)
    return calculator.calculate_cost(input_tokens, output_tokens)


def compare_model_costs(
    input_tokens: int,
    output_tokens: int,
    model_names: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to compare costs across models.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_names: List of models to compare

    Returns:
        List of cost comparisons
    """
    # Use any model for the comparison function
    from .models import MODEL_DATABASE
    first_model = list(MODEL_DATABASE.keys())[0]
    calculator = CostCalculator(first_model)
    return calculator.compare_models(input_tokens, output_tokens, model_names)
