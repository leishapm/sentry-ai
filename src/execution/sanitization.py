"""Helpers for preventing secrets from reaching audit storage or the reasoner."""

import re
from collections.abc import Mapping
from typing import Any

from src.execution.schemas import ToolExecutionRequest

SENSITIVE_KEY_PARTS = frozenset(
    {"apikey", "authorization", "password", "privatekey", "secret", "token", "credential"}
)
REDACTED = "[REDACTED]"
_BEARER_RE = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")
_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|password|secret|private[_-]?key)\s*[=:]\s*)"
    r"([^\s,;]+)"
)


def is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _redact_text(value: str) -> str:
    value = _BEARER_RE.sub(rf"\1{REDACTED}", value)
    return _ASSIGNMENT_RE.sub(rf"\1{REDACTED}", value)


def redact_value(value: Any) -> Any:
    """Recursively redact credential-like fields and common inline formats."""
    if isinstance(value, Mapping):
        return {
            key: REDACTED if isinstance(key, str) and is_sensitive_key(key) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def contains_credential(value: Any) -> bool:
    """Detect named credential fields and common inline credential formats."""
    if isinstance(value, Mapping):
        return any(
            (isinstance(key, str) and is_sensitive_key(key)) or contains_credential(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(contains_credential(item) for item in value)
    return isinstance(value, str) and _redact_text(value) != value


def redact_execution_request(request: ToolExecutionRequest) -> ToolExecutionRequest:
    """Return a safe copy for persistence and external reasoning calls."""
    return request.model_copy(
        update={
            "agent_name": redact_value(request.agent_name),
            "tool_name": redact_value(request.tool_name),
            "action": redact_value(request.action),
            "parameters": redact_value(request.parameters),
            "requested_scope": redact_value(request.requested_scope),
            "allowed_scopes": redact_value(request.allowed_scopes),
            "context": redact_value(request.context),
        }
    )
