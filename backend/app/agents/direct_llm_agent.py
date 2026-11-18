import datetime
import time
from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgentAdapter, AgentExecutionResult
from app.providers.provider_factory import ProviderFactory
from app.execution.tools import ToolRegistry
from app.utils.redaction import redact_sensitive_data


class DirectLLMAgent(BaseAgentAdapter):
    """
    Direct LLM Tool-Calling Agent.
    Coordinates prompting, provider invocation, tool dispatch, and trace collection.
    """
    async def execute(self, user_input: str) -> AgentExecutionResult:
        start_time = time.time()
        provider_name = self.config.get("provider", "mock")
        model_name = self.config.get("model_name", "mock-agent")
        system_prompt = self.config.get("system_prompt", "")
        temperature = float(self.config.get("temperature", 0.2))
        max_tokens = int(self.config.get("max_output_tokens", 2048))
        tools = self.config.get("tools", [])
        output_format = self.config.get("output_format", "text")

        trace_steps: List[Dict[str, Any]] = [
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "event_type": "USER_INPUT",
                "content": user_input
            }
        ]

        try:
            provider = ProviderFactory.get_provider(
                provider_name=provider_name,
                model_name=model_name,
                api_key=self.api_key
            )

            schema_req = {"type": "object"} if output_format == "json" else None

            # Turn 1: Model generation
            response = await provider.generate(
                prompt=user_input,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                json_schema=schema_req
            )

            raw_tool_calls = [
                {"tool_name": tc.tool_name, "arguments": tc.arguments, "call_id": tc.call_id}
                for tc in response.tool_calls
            ]
            tool_results = []

            # Trace model response
            trace_steps.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "event_type": "AGENT_DECISION",
                "content": {
                    "text": response.text,
                    "tool_calls": raw_tool_calls
                }
            })

            # Execute tool calls if any
            final_text = response.text
            for tc in response.tool_calls:
                t_start = time.time()
                t_res = ToolRegistry.execute_tool(tc.tool_name, tc.arguments)
                t_duration = int((time.time() - t_start) * 1000)

                tool_results.append({
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "result": t_res,
                    "duration_ms": t_duration
                })

                trace_steps.append({
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "event_type": "TOOL_EXECUTION",
                    "content": {
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "result": t_res
                    }
                })

            # If tool was called and final text was just an acknowledgment, format comprehensive response
            if response.tool_calls and tool_results:
                summary_lines = []
                for tr in tool_results:
                    res_data = tr["result"]
                    if res_data.get("success"):
                        if tr["tool_name"] == "get_order":
                            d = res_data.get("data", {})
                            summary_lines.append(f"Order {d.get('order_id')}: Status is {d.get('status')}. Tracking: {d.get('tracking_number', 'N/A')}.")
                        elif tr["tool_name"] == "check_refund_eligibility":
                            summary_lines.append(f"Order {tr['arguments'].get('order_id')}: Refund eligible: {res_data.get('eligible')}. Reason: {res_data.get('reason', res_data.get('message', ''))}.")
                        elif tr["tool_name"] == "search_products":
                            summary_lines.append(f"Found {res_data.get('results_count', 0)} matching products in catalog.")
                        elif tr["tool_name"] == "get_weather":
                            w = res_data.get("weather", {})
                            summary_lines.append(f"Weather for {w.get('location')}: {w.get('condition')}. Shipping: {w.get('shipping_delays')}.")
                    else:
                        summary_lines.append(f"Tool {tr['tool_name']} report: {res_data.get('error')}")

                if summary_lines and not (output_format == "json"):
                    final_text = " ".join(summary_lines)

            total_duration_ms = int((time.time() - start_time) * 1000)

            trace_steps.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "event_type": "FINAL_OUTPUT",
                "content": final_text
            })

            # Clean and redact trace
            safe_trace = redact_sensitive_data(trace_steps)

            return AgentExecutionResult(
                final_response=final_text,
                tool_calls=raw_tool_calls,
                tool_results=tool_results,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.total_tokens,
                duration_ms=total_duration_ms,
                provider=provider_name,
                model_name=response.model_name or model_name,
                trace_steps=safe_trace
            )

        except Exception as e:
            total_duration_ms = int((time.time() - start_time) * 1000)
            trace_steps.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "event_type": "ERROR",
                "content": str(e)
            })
            return AgentExecutionResult(
                final_response="",
                tool_calls=[],
                tool_results=[],
                duration_ms=total_duration_ms,
                provider=provider_name,
                model_name=model_name,
                error=str(e),
                trace_steps=redact_sensitive_data(trace_steps)
            )
