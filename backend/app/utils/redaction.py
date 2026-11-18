import re
from typing import Any, Dict, List, Union

# Regex patterns matching popular API keys and credential tokens
PATTERNS = [
    # OpenAI API keys
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"), "[REDACTED_OPENAI_KEY]"),
    # Google API keys
    (re.compile(r"AIza[0-9A-Za-z\-_]{25,50}"), "[REDACTED_GEMINI_KEY]"),
    # Generic Bearer tokens
    (re.compile(r"Bearer\s+([a-zA-Z0-9\-_.]+)", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Standard JWT tokens
    (re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"), "[REDACTED_JWT]"),
    # AWS access keys
    (re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
]

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "private_key",
    "openai_api_key",
    "gemini_api_key",
}


def redact_string(text: str) -> str:
    """Redact sensitive API keys and tokens from a string."""
    if not isinstance(text, str):
        return text
    result = text
    for pattern, replacement in PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_sensitive_data(obj: Any) -> Any:
    """Recursively redact sensitive keys and values from dicts, lists, or strings."""
    if isinstance(obj, dict):
        cleaned: Dict[str, Any] = {}
        for key, value in obj.items():
            lower_key = str(key).lower()
            if any(s in lower_key for s in SENSITIVE_KEYS):
                cleaned[key] = "[REDACTED_SECRET]"
            else:
                cleaned[key] = redact_sensitive_data(value)
        return cleaned
    elif isinstance(obj, list):
        return [redact_sensitive_data(item) for item in obj]
    elif isinstance(obj, str):
        return redact_string(obj)
    return obj
