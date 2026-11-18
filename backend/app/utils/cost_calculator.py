from typing import Dict, Tuple

# Pricing per 1,000,000 tokens (USD)
# Format: model_key: (input_cost_per_million, output_cost_per_million)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI models
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-2024-08-06": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    
    # Gemini models
    "gemini-1.5-pro": (1.25, 5.00),
    "gemini-1.5-pro-latest": (1.25, 5.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-flash-latest": (0.075, 0.30),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-exp": (0.10, 0.40),
    
    # Mock / Demo model
    "mock-agent": (0.00, 0.00),
    "demo-support-agent": (0.00, 0.00),
}


def calculate_token_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate estimated cost in USD for the given model and token counts.
    Returns estimated cost rounded to 6 decimal places.
    """
    normalized = model_name.lower().strip()
    
    # Find matching model
    rates = None
    for key, price in MODEL_PRICING.items():
        if key in normalized:
            rates = price
            break
            
    if rates is None:
        # Default fallback estimate (average mid-tier model pricing: $1.00 input, $4.00 output per 1M)
        rates = (1.00, 4.00)
        
    input_rate, output_rate = rates
    cost = (input_tokens / 1_000_000.0) * input_rate + (output_tokens / 1_000_000.0) * output_rate
    return round(cost, 6)
