"""HTTP client for Ollama (VentanaAI window analysis)."""

from __future__ import annotations

import base64
import json
import logging
import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.ventana import VentanaAnalysisResult

_logger = logging.getLogger("entropia")

# =========================
# PROMPT
# =========================

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


# =========================
# IMAGE
# =========================

def _image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# =========================
# RESPONSE CLEANING
# =========================

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


# =========================
# RESPONSE MAPPING
# =========================

def _message_to_result(data: dict[str, Any]) -> VentanaAnalysisResult:
    text = ""

    r = data.get("response")
    if isinstance(r, str):
        text = r

    if not text:
        raise ValueError("Ollama response contained no usable text")

    parsed = _parse_json_object(text)

    desc = parsed.get("description")
    if not isinstance(desc, str):
        raise ValueError('"description" must be a string in JSON response')

    sd = parsed.get("structured_data")
    if sd is not None and not isinstance(sd, (dict, list)):
        raise ValueError('"structured_data" must be object, array or null')

    return VentanaAnalysisResult(
        description=desc,
        structured_data=sd,
    )


# =========================
# MODEL WAIT
# =========================

async def _wait_for_model(base_url: str, model: str, timeout: int = 60):
    deadline = asyncio.get_event_loop().time() + timeout

    async with httpx.AsyncClient() as client:
        while asyncio.get_event_loop().time() < deadline:
            try:
                res = await client.get(f"{base_url}/api/tags")
                res.raise_for_status()

                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]

                _logger.info("OLLAMA MODELS: %s", models)

                if model in models:
                    _logger.info("Model ready: %s", model)
                    return

            except Exception as e:
                _logger.warning("Ollama health error: %s", e)

            await asyncio.sleep(2)

    raise TimeoutError(f"Model {model} not ready after {timeout}s")


# =========================
# RETRY LOGIC
# =========================

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


# =========================
# MAIN FUNCTION
# =========================

async def analyze_with_ventana(
    *,
    user_prompt: str,
    image_path: str,
    model: str | None = None,
) -> VentanaAnalysisResult:
    """
    Call Ollama /api/generate with image + prompt.

    ✔ Envía imagen en base64
    ✔ Fuerza salida JSON
    ✔ Retry automático
    ✔ Espera a que el modelo esté listo (🔥 fix crítico)
    """

    base = settings.ollama_base_url.rstrip("/")
    model_name = model or settings.ollama_model
    timeout = httpx.Timeout(settings.ollama_timeout)

    # 🔥 Esperar modelo disponible
    await _wait_for_model(base, model_name)

    # 🔥 Convertir imagen
    try:
        image_b64 = _image_to_base64(image_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read image at {image_path}: {e}")

    payload: dict[str, Any] = {
        "model": model_name,
        "prompt": _build_prompt(user_prompt),
        "images": [image_b64],
        "stream": False,
    }

    url = f"{base}/api/generate"

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                _logger.debug("Ollama response: %s", response.text)
                body = response.json()

            return _message_to_result(body)

        except Exception as exc:
            if attempt == 0 and _is_retryable(exc):
                _logger.warning(
                    "Ollama VentanaAI request failed (retrying once): %s",
                    exc,
                )
                await asyncio.sleep(2)
                continue

            _logger.error("Ollama VentanaAI request failed: %s", exc)

            # 🔥 FALLBACK requerido por el reto
            return VentanaAnalysisResult(
                description="Descripción pendiente de procesamiento",
                structured_data=None,
            )