import logging
import sys
from app.config import settings
from app.utils.redaction import redact_string


class RedactingFormatter(logging.Formatter):
    """Custom logging formatter that strips sensitive API keys and tokens."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_string(original)


def setup_logging():
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = RedactingFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Remove existing handlers to avoid duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)


logger = logging.getLogger("agentbench")
