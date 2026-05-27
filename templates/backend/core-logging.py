"""
Structured logging configuration for all projects.

Provides:
- JSON-formatted structured logs (production) or colored console (development)
- Automatic secret redaction via ScrubProcessor
- Correlation ID propagation (trace_id) for request tracing
- Standard fields: timestamp, level, service, logger, trace_id
- Log level from environment (LOG_LEVEL env var, default INFO)

Usage:
    from core.logging import get_logger, configure_logging, correlation_id_var

    # At app startup (main.py / lifespan):
    configure_logging(service_name="my-service")

    # In any module:
    log = get_logger(__name__)
    log.info("user_created", user_id=42, email="redacted@example.com")

    # Correlation IDs — set in middleware, propagated automatically:
    correlation_id_var.set("abc-123")
    log.info("processing_request")  # trace_id: "abc-123" added automatically

FastAPI middleware example:
    @app.middleware("http")
    async def correlation_middleware(request, call_next):
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        correlation_id_var.set(trace_id)
        response = await call_next(request)
        response.headers["x-trace-id"] = trace_id
        return response
"""

import os
import re
import sys
import logging
from contextvars import ContextVar

import structlog

# --- Correlation ID ---
correlation_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


# --- Secret Redaction ---
SCRUB_PATTERNS = [
    # Connection strings (ODBC, JDBC, SQLAlchemy)
    re.compile(r"(password|pwd|Password)=[^;]+", re.IGNORECASE),
    re.compile(r"AccountKey=[A-Za-z0-9+/=]+", re.IGNORECASE),
    # Bearer tokens
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    # Azure SAS tokens
    re.compile(r"sig=[A-Za-z0-9%]+"),
    # Generic secret-like keys
    re.compile(r"(api[_-]?key|secret|token|authorization)=[^\s&]+", re.IGNORECASE),
]
REDACTED = "[REDACTED]"

# Keys whose values should always be fully redacted
SENSITIVE_KEYS = frozenset({
    "password", "secret", "token", "api_key", "apikey",
    "authorization", "access_token", "refresh_token",
    "private_key", "client_secret",
})


class ScrubProcessor:
    """Structlog processor that redacts secrets from log event values."""

    def __call__(self, logger, method, event_dict):
        for key, value in list(event_dict.items()):
            if key in SENSITIVE_KEYS:
                event_dict[key] = REDACTED
            elif isinstance(value, str):
                for pattern in SCRUB_PATTERNS:
                    value = pattern.sub(REDACTED, value)
                event_dict[key] = value
        return event_dict


# --- Correlation ID Injection ---
class CorrelationIdProcessor:
    """Injects trace_id from the current context into every log event."""

    def __call__(self, logger, method, event_dict):
        trace_id = correlation_id_var.get()
        if trace_id is not None:
            event_dict.setdefault("trace_id", trace_id)
        return event_dict


# --- Configuration ---
def configure_logging(
    service_name: str,
    log_level: str | None = None,
    json_output: bool | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        service_name: Name added to every log event as 'service' field.
        log_level: Override log level (default: LOG_LEVEL env var or INFO).
        json_output: Force JSON (True) or console (False). Default: JSON
                     unless LOG_FORMAT=console or DEBUG is set.
    """
    level = (log_level or os.environ.get("LOG_LEVEL", "INFO")).upper()

    if json_output is None:
        json_output = os.environ.get("LOG_FORMAT", "json").lower() != "console"

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        CorrelationIdProcessor(),
        ScrubProcessor(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Bind service name globally
    structlog.contextvars.bind_contextvars(service=service_name)

    # Quiet noisy libraries
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger bound to the given module name."""
    return structlog.get_logger(name)
