"""HTTP client for Ollama (VentanaAI window analysis)."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.ventana import VentanaAnalysisResult

_logger = logging.getLogger("entropia")

VENTANA_PROMPT_PREFIX = (
    "You are VentanaAI, a specialized window analysis model trained by Entropia.ai."
)

_JSON_TAIL = (
    '\n\nRespond with a single JSON object only, using this exact shape: '
    '{"description": "<string>", "structured_data": <object or null>}. '
    "Do not wrap the JSON in markdown code fences."
)


def _build_prompt(user_prompt: str) -> str:
    text = user_prompt.strip()
    return f"{VENTANA_PROMPT_PREFIX}\n\n{text}{_JSON_TAIL}"


def _strip_code_fence(raw: str) -> str:
    s = raw.strip()
    if not s.startswith("```"):
        return s
    _, _, rest = s.partition("\n")
    if "```" in rest:
        return rest.rsplit("```", 1)[0].strip()
    return rest.removeprefix("```json").removeprefix("```").strip()


def _parse_json_object(content: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(content)
    return json.loads(cleaned)


def _message_to_result(data: dict[str, Any]) -> VentanaAnalysisResult:
    msg = data.get("message")
    text = ""
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, str):
            text = c
    if not text:
        r = data.get("response")
        if isinstance(r, str):
            text = r
    if not text:
        raise ValueError("Ollama response contained no message content")

    parsed = _parse_json_object(text)
    desc = parsed.get("description")
    if not isinstance(desc, str):
        raise ValueError('"description" must be a string in the JSON response')
    sd = parsed.get("structured_data")
    if sd is not None and not isinstance(sd, (dict, list)):
        raise ValueError('"structured_data" must be an object, array, or null')
    return VentanaAnalysisResult(description=desc, structured_data=sd)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.WriteError,
        ),
    ):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    if isinstance(exc, (json.JSONDecodeError, ValueError, TypeError, KeyError)):
        return True
    return False


async def analyze_with_ventana(
    *,
    user_prompt: str,
    model: str | None = None,
) -> VentanaAnalysisResult:
    """
    Call Ollama ``/api/chat`` with a prompt that starts with the VentanaAI prefix.

    Uses a 30s client timeout (configurable) and retries the full request once on
    retryable failures (timeouts, transport errors, 5xx, or invalid JSON shape).
    """
    base = settings.ollama_base_url.rstrip("/")
    model_name = model or settings.ollama_model
    timeout = httpx.Timeout(settings.ollama_timeout_seconds)
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [{"role": "user", "content": _build_prompt(user_prompt)}],
        "stream": False,
        "format": "json",
    }
    url = f"{base}/api/chat"

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                body = response.json()
            return _message_to_result(body)
        except Exception as exc:
            if attempt == 0 and _is_retryable(exc):
                _logger.warning(
                    "Ollama VentanaAI request failed (will retry once): %s",
                    exc,
                )
                continue
            raise
