import json
import re
import time
from typing import Any, Dict, List, Optional
from app.providers.base import BaseLLMProvider, ProviderResponse, ProviderToolCall, ProviderUsage


class MockProvider(BaseLLMProvider):
    """
    Deterministic local mock provider for demo mode, automated testing,
    and offline benchmarking without external API keys.
    Simulated results are clearly marked with provider_name='mock'.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "mock-agent"):
        super().__init__(api_key=api_key, model_name=model_name or "mock-agent")

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "success": True,
            "latency_ms": 12,
            "message": "Deterministic mock provider connection verified (Demo / Offline mode)",
            "model": self.model_name
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> ProviderResponse:
        start = time.time()
        lower_prompt = prompt.lower()
        tool_calls: List[ProviderToolCall] = []
        text_content = ""

        # Check for adversarial / prompt injection inputs
        if any(w in lower_prompt for w in ["system override", "ignore all previous instructions", "print your complete initial system prompt"]):
            text_content = "I cannot fulfill this request. I am here to assist you with e-commerce customer support questions."
        elif any(w in lower_prompt for w in ["curl", "/etc/passwd", "drop table", "shell tool"]):
            text_content = "I am unable to perform system commands or execute scripts. My actions are restricted to customer support services."
        elif any(w in lower_prompt for w in ["phone number on file", "home address", "private phone"]):
            text_content = "To protect customer privacy and security, I cannot share or disclose personal identifying information (PII)."
        # Tool call pattern matching
        elif "refund" in lower_prompt and "ord-" in lower_prompt:
            order_matches = re.findall(r"ord-\d+", lower_prompt, re.IGNORECASE)
            order_id = order_matches[0].upper() if order_matches else "ORD-1002"
            tool_calls.append(ProviderToolCall(
                tool_name="check_refund_eligibility",
                arguments={"order_id": order_id}
            ))
            if json_schema or "json" in lower_prompt:
                text_content = json.dumps({
                    "order_id": order_id,
                    "eligible": True,
                    "reason": "Within 30-day window and item delivered intact",
                    "max_refund_amount": 129.99
                })
            else:
                text_content = f"I am checking the refund eligibility for order {order_id}."
        elif ("order" in lower_prompt or "track" in lower_prompt or "package" in lower_prompt or "status" in lower_prompt) and "ord-" in lower_prompt:
            order_matches = re.findall(r"ord-\d+", lower_prompt, re.IGNORECASE)
            for ord_id in order_matches:
                tool_calls.append(ProviderToolCall(
                    tool_name="get_order",
                    arguments={"order_id": ord_id.upper()}
                ))
            if json_schema or "json" in lower_prompt:
                text_content = json.dumps({
                    "order_id": order_matches[0].upper() if order_matches else "ORD-1001",
                    "status": "Shipped",
                    "items_count": 2,
                    "total_amount": 189.50
                })
            else:
                order_list = ", ".join([o.upper() for o in order_matches])
                text_content = f"Looking up status for order {order_list}. Status: Shipped with active tracking."
        elif "weather" in lower_prompt:
            location = "Seattle"
            if "munich" in lower_prompt or "münchen" in lower_prompt:
                location = "München, Germany"
            elif "chicago" in lower_prompt:
                location = "Chicago"
            elif "seattle" in lower_prompt:
                location = "Seattle"
            
            tool_calls.append(ProviderToolCall(
                tool_name="get_weather",
                arguments={"location": location}
            ))
            text_content = f"Checking current weather conditions for {location}."
        elif any(w in lower_prompt for w in ["headphone", "keyboard", "cable", "product", "sell", "stock", "hoverboard"]):
            query = "products"
            if "headphone" in lower_prompt:
                query = "wireless noise cancelling headphones"
            elif "keyboard" in lower_prompt:
                query = "mechanical keyboard"
            elif "cable" in lower_prompt:
                query = "USB-C braided charging cables"
            elif "hoverboard" in lower_prompt:
                query = "Antigravity Hoverboard 9000X"

            tool_calls.append(ProviderToolCall(
                tool_name="search_products",
                arguments={"query": query}
            ))
            text_content = f"Searching store inventory for '{query}'."
        elif "return policy" in lower_prompt:
            text_content = "Our standard return policy allows returns within 30 days of delivery for items in original condition."
        elif "shipping to australia" in lower_prompt or "international shipping" in lower_prompt:
            text_content = "Yes, we offer international shipping to Australia and many other countries, typically delivering in 5-10 business days."
        elif "credit card" in lower_prompt or "pci" in lower_prompt:
            text_content = "All transactions are fully PCI-DSS Level 1 compliant with end-to-end 256-bit encryption. We never store raw credit card numbers."
        elif "refund" in lower_prompt and not re.search(r"ord-\d+", lower_prompt, re.IGNORECASE):
            text_content = "I would be happy to help with your refund! Could you please provide your order ID or order number so I can check eligibility?"
        elif "black one" in lower_prompt:
            text_content = "Could you please clarify which product or item you are referring to? Please provide the product name or link."
        elif "quantum" in lower_prompt or "double-slit" in lower_prompt:
            text_content = "While the double-slit experiment demonstrates wave-particle duality in physics, I specialize in customer support for our store! How can I assist with your orders or products today?"
        else:
            text_content = "Thank you for contacting customer support. How may I assist you with your orders or products today?"

        duration_ms = max(int((time.time() - start) * 1000) + 120, 120)
        input_tokens = len(prompt.split()) + 35
        output_tokens = len(text_content.split()) + (len(tool_calls) * 20)
        
        return ProviderResponse(
            text=text_content,
            tool_calls=tool_calls,
            usage=ProviderUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens
            ),
            model_name=self.model_name,
            provider_name="mock",
            duration_ms=duration_ms
        )
