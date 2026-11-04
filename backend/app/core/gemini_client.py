"""Resilient Gemini AI Client.

Features:
- Configurable timeout and fallback models priority list.
- Up to 3 retries with exponential backoff and jitter on 429, 500, 503 and timeouts.
- Automatic fallback to next configured model when retries are exhausted.
- Masked logging ensuring no secrets are printed in logs or error traces.
- Shared module used across agent, embeddings, and setup check.
"""

import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import httpx

from app.core.config import settings

logger = logging.getLogger("nightwatch.gemini")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
RETRYABLE_STATUS_CODES = {429, 500, 503}


class GeminiError(Exception):
    """Base exception for all Gemini client errors."""
    pass


class GeminiConfigError(GeminiError):
    """Raised when required configuration (e.g., API key) is missing."""
    pass


class GeminiRequestError(GeminiError):
    """Raised when all configured models and retry attempts fail."""
    pass


@dataclass
class GeminiResponse:
    """Response returned from generate_content."""
    text: str
    model: str
    duration_seconds: float
    raw: Dict[str, Any]


@dataclass
class GeminiEmbeddingResponse:
    """Response returned from embed_content."""
    embedding: List[float]
    model: str
    duration_seconds: float
    raw: Dict[str, Any]


def _mask_secret(secret: Optional[str]) -> str:
    """Mask sensitive string showing only the last 4 characters."""
    if not secret:
        return "(none)"
    s = secret.strip()
    if len(s) <= 4:
        return "****"
    return f"{'*' * (len(s) - 4)}{s[-4:]}"


def _sanitize_message(message: str, secret: Optional[str]) -> str:
    """Scrub cleartext secret from message if present."""
    if secret and secret in message:
        return message.replace(secret, _mask_secret(secret))
    return message


class GeminiClient:
    """Resilient client for Google Gemini REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        http_client: Optional[httpx.Client] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.fallback_models = (
            fallback_models
            if fallback_models is not None
            else settings.gemini_fallback_models_list
        )
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.GEMINI_TIMEOUT_SECONDS
        )
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._custom_http_client = http_client
        self.sleep_fn = sleep_fn or time.sleep

    def _get_http_client(self) -> httpx.Client:
        if self._custom_http_client is not None:
            return self._custom_http_client
        return httpx.Client(timeout=self.timeout_seconds)

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        # attempt: 1 for 1st retry, 2 for 2nd retry, etc.
        backoff = self.base_delay * (2 ** (attempt - 1))
        # Add jitter between 0% and 50% of the backoff
        jitter = random.uniform(0.0, backoff * 0.5)
        return backoff + jitter

    def _execute_with_retry_and_fallback(
        self,
        action: str,
        payload_builder: Callable[[str], Dict[str, Any]],
        target_model: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str, float]:
        """Execute request with retries per model and fallback model traversal."""
        if not self.api_key:
            raise GeminiConfigError(
                "GEMINI_API_KEY is not configured. Provide it via .env or GEMINI_API_KEY."
            )

        # Build priority model list
        primary = target_model or self.model
        models_to_try: List[str] = [primary]
        if action == "generateContent":
            for fb in self.fallback_models:
                if fb and fb not in models_to_try:
                    models_to_try.append(fb)

        client = self._get_http_client()
        last_error_desc = "Unknown error"

        for m_idx, current_model in enumerate(models_to_try):
            url = f"{GEMINI_BASE_URL}/models/{current_model}:{action}"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }
            body = payload_builder(current_model)

            for attempt in range(self.max_retries + 1):
                # If this is a retry attempt, sleep with backoff & jitter
                if attempt > 0:
                    sleep_time = self._calculate_backoff(attempt)
                    logger.warning(
                        "Gemini [%s] call to '%s' failed (reason: %s). "
                        "Retrying in %.2fs (retry %d/%d)...",
                        action,
                        current_model,
                        last_error_desc,
                        sleep_time,
                        attempt,
                        self.max_retries,
                    )
                    self.sleep_fn(sleep_time)

                start_time = time.monotonic()
                try:
                    resp = client.post(
                        url,
                        headers=headers,
                        json=body,
                        timeout=self.timeout_seconds,
                    )
                    duration = time.monotonic() - start_time

                    if resp.status_code == 200:
                        return resp.json(), current_model, duration

                    # Check retryable status codes: 429, 500, 503
                    if resp.status_code in RETRYABLE_STATUS_CODES:
                        last_error_desc = f"HTTP {resp.status_code}"
                        # Retry on current model
                        continue

                    # Non-retryable status (e.g., 400 Bad Request, 404 Not Found)
                    raw_err = _sanitize_message(resp.text[:140], self.api_key)
                    last_error_desc = f"HTTP {resp.status_code} ({raw_err})"
                    logger.warning(
                        "Gemini [%s] call to '%s' encountered non-retryable error: %s",
                        action,
                        current_model,
                        last_error_desc,
                    )
                    # Break out of attempt loop to try next fallback model
                    break

                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    err_name = type(exc).__name__
                    last_error_desc = f"{err_name}: timeout or network error"
                    # Retry on current model
                    continue
                except Exception as exc:
                    err_msg = _sanitize_message(str(exc), self.api_key)
                    last_error_desc = f"Unexpected exception: {err_msg}"
                    break

            # If all attempts exhausted for current model, log fallback
            if m_idx + 1 < len(models_to_try):
                next_model = models_to_try[m_idx + 1]
                logger.warning(
                    "Gemini [%s] model '%s' exhausted all attempts (%s). "
                    "Falling back to next model '%s'...",
                    action,
                    current_model,
                    last_error_desc,
                    next_model,
                )

        # If all models exhausted
        logger.error(
            "Gemini [%s] all configured models failed (%s). Last error: %s",
            action,
            ", ".join(models_to_try),
            last_error_desc,
        )
        raise GeminiRequestError(
            f"All configured Gemini models failed ({', '.join(models_to_try)}). "
            f"Last error: {last_error_desc}"
        )

    def generate_content(
        self,
        prompt_or_contents: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> GeminiResponse:
        """Send prompt to Gemini with resilient retry and model fallback."""
        if isinstance(prompt_or_contents, str):
            contents = [{"parts": [{"text": prompt_or_contents}]}]
        else:
            contents = prompt_or_contents

        config = dict(generation_config or {})
        if max_output_tokens is not None:
            config["maxOutputTokens"] = max_output_tokens
        if temperature is not None:
            config["temperature"] = temperature

        def payload_builder(_target: str) -> Dict[str, Any]:
            p: Dict[str, Any] = {"contents": contents}
            if config:
                p["generationConfig"] = config
            return p

        data, answered_model, duration = self._execute_with_retry_and_fallback(
            action="generateContent",
            payload_builder=payload_builder,
            target_model=model,
        )

        # Extract generated text
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(part.get("text", "") for part in parts).strip()
            else:
                text = ""
        except Exception:
            text = ""

        return GeminiResponse(
            text=text,
            model=answered_model,
            duration_seconds=duration,
            raw=data,
        )

    def embed_content(
        self,
        text: str,
        model: Optional[str] = "text-embedding-004",
    ) -> GeminiEmbeddingResponse:
        """Generate text embedding vector with resilient retry and fallback."""
        def payload_builder(target_m: str) -> Dict[str, Any]:
            return {
                "model": f"models/{target_m}",
                "content": {"parts": [{"text": text}]},
            }

        data, answered_model, duration = self._execute_with_retry_and_fallback(
            action="embedContent",
            payload_builder=payload_builder,
            target_model=model,
        )

        embedding = data.get("embedding", {}).get("values", [])
        return GeminiEmbeddingResponse(
            embedding=embedding,
            model=answered_model,
            duration_seconds=duration,
            raw=data,
        )


_shared_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Return shared GeminiClient instance configured from settings."""
    global _shared_gemini_client
    if _shared_gemini_client is None:
        _shared_gemini_client = GeminiClient()
    return _shared_gemini_client
