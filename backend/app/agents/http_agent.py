import datetime
import ipaddress
import socket
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from app.agents.base import BaseAgentAdapter, AgentExecutionResult
from app.core.errors import BadRequestException
from app.utils.redaction import redact_sensitive_data


def validate_safe_url(url_str: str) -> bool:
    """SSRF protection: prevent requests to localhost, internal network, or metadata services."""
    parsed = urlparse(url_str)
    if parsed.scheme not in ["http", "https"]:
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    
    if hostname.lower() in ["localhost", "127.0.0.1", "::1", "metadata.google.internal"]:
        return False

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except Exception:
        # If DNS resolution fails, allow httpx to fail gracefully
        pass
    return True


class HttpAgent(BaseAgentAdapter):
    """
    Adapter for external HTTP-based AI agents.
    Dispatches request to an external agent endpoint with SSRF protections.
    """
    async def execute(self, user_input: str) -> AgentExecutionResult:
        endpoint = self.config.get("http_endpoint")
        if not endpoint:
            return AgentExecutionResult(
                final_response="",
                error="No HTTP endpoint configured for this external agent.",
                duration_ms=0,
                provider="http"
            )

        if not validate_safe_url(endpoint):
            return AgentExecutionResult(
                final_response="",
                error="Security violation: HTTP agent destination resolves to a restricted local or internal address (SSRF blocked).",
                duration_ms=0,
                provider="http"
            )

        start_time = time.time()
        trace_steps: List[Dict[str, Any]] = [
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "event_type": "HTTP_DISPATCH",
                "content": {"endpoint": endpoint, "input": user_input}
            }
        ]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(endpoint, json={"prompt": user_input, "config": self.config})
                duration_ms = int((time.time() - start_time) * 1000)
                
                if res.status_code != 200:
                    return AgentExecutionResult(
                        final_response="",
                        error=f"External agent returned HTTP {res.status_code}: {res.text}",
                        duration_ms=duration_ms,
                        provider="http",
                        trace_steps=trace_steps
                    )
                
                data = res.json()
                final_response = data.get("response", data.get("text", res.text))
                tool_calls = data.get("tool_calls", [])
                
                trace_steps.append({
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "event_type": "HTTP_RESPONSE",
                    "content": data
                })

                return AgentExecutionResult(
                    final_response=final_response,
                    tool_calls=tool_calls,
                    duration_ms=duration_ms,
                    provider="http",
                    model_name="external-http",
                    trace_steps=redact_sensitive_data(trace_steps)
                )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentExecutionResult(
                final_response="",
                error=f"Failed to communicate with external agent: {str(e)}",
                duration_ms=duration_ms,
                provider="http",
                trace_steps=trace_steps
            )
