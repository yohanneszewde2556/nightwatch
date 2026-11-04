"""Unit tests for resilient Gemini client (retry, backoff, jitter, fallback, and masking)."""

import logging
from typing import List
import httpx
import pytest

from app.core.gemini_client import (
    GeminiClient,
    GeminiConfigError,
    GeminiEmbeddingResponse,
    GeminiRequestError,
    GeminiResponse,
)


def make_mock_gemini_response(text: str = "Test response") -> dict:
    """Helper to create standard Gemini API generateContent response payload."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": text}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ]
    }


def make_mock_embedding_response(values: List[float] = None) -> dict:
    """Helper to create standard Gemini API embedContent response payload."""
    return {
        "embedding": {
            "values": values or [0.1, 0.2, 0.3, 0.4]
        }
    }


def test_gemini_success_primary_model():
    """Verify primary model succeeds immediately on first attempt without retries."""
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert "gemini-2.5-flash" in str(request.url)
        assert request.headers.get("x-goog-api-key") == "test-key-1234"
        return httpx.Response(200, json=make_mock_gemini_response("Hello from primary!"))

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        fallback_models=["gemini-2.0-flash"],
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    resp = client.generate_content("Say hello")
    assert isinstance(resp, GeminiResponse)
    assert resp.text == "Hello from primary!"
    assert resp.model == "gemini-2.5-flash"
    assert resp.duration_seconds >= 0.0
    assert len(sleep_calls) == 0  # No retries


def test_gemini_retry_on_429_then_succeed():
    """Verify 429 triggers retry with backoff and then succeeds on primary model."""
    call_count = 0
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            # First two calls hit rate limit 429
            return httpx.Response(429, json={"error": "ResourceExhausted"})
        # 3rd attempt succeeds
        return httpx.Response(200, json=make_mock_gemini_response("Recovered after 429!"))

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        fallback_models=["gemini-2.0-flash"],
        base_delay=0.1,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    resp = client.generate_content("Test 429 retry")
    assert resp.text == "Recovered after 429!"
    assert resp.model == "gemini-2.5-flash"
    assert call_count == 3
    assert len(sleep_calls) == 2
    # Verify exponential backoff growth
    assert sleep_calls[1] > sleep_calls[0]


def test_gemini_retry_on_500_and_503():
    """Verify 500 and 503 server errors trigger retries."""
    call_count = 0
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(500, json={"error": "Internal server error"})
        if call_count == 2:
            return httpx.Response(503, json={"error": "Service unavailable"})
        return httpx.Response(200, json=make_mock_gemini_response("Recovered from server errors!"))

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        base_delay=0.1,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    resp = client.generate_content("Test 500/503")
    assert resp.text == "Recovered from server errors!"
    assert call_count == 3
    assert len(sleep_calls) == 2


def test_gemini_retry_on_timeout():
    """Verify httpx.ReadTimeout triggers retry."""
    call_count = 0
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ReadTimeout("Read timed out after 60s")
        return httpx.Response(200, json=make_mock_gemini_response("Success after timeout!"))

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        base_delay=0.1,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    resp = client.generate_content("Test timeout")
    assert resp.text == "Success after timeout!"
    assert call_count == 2
    assert len(sleep_calls) == 1


def test_gemini_fallback_when_primary_exhausts_retries():
    """Verify fallback model is engaged after primary model exhausts all 3 retries (4 calls total)."""
    requests_log = []
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        requests_log.append(url_str)
        if "gemini-2.5-flash" in url_str:
            # Primary model always fails 429
            return httpx.Response(429, json={"error": "Quota exhausted"})
        elif "gemini-2.0-flash" in url_str:
            # Fallback model succeeds
            return httpx.Response(200, json=make_mock_gemini_response("Answered by fallback!"))
        return httpx.Response(404, text="Unknown model")

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        fallback_models=["gemini-2.0-flash"],
        max_retries=3,
        base_delay=0.1,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    resp = client.generate_content("Test fallback")
    assert resp.text == "Answered by fallback!"
    assert resp.model == "gemini-2.0-flash"

    # Primary model attempted 1 initial + 3 retries = 4 times
    primary_calls = [u for u in requests_log if "gemini-2.5-flash" in u]
    fallback_calls = [u for u in requests_log if "gemini-2.0-flash" in u]
    assert len(primary_calls) == 4
    assert len(fallback_calls) == 1
    assert len(sleep_calls) == 3


def test_gemini_multiple_fallbacks_in_order():
    """Verify client walks through multiple fallback models in priority order."""
    models_called = []
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "gemini-primary" in url_str:
            models_called.append("gemini-primary")
            return httpx.Response(503, json={"error": "Service unavailable"})
        elif "gemini-fallback-1" in url_str:
            models_called.append("gemini-fallback-1")
            return httpx.Response(500, json={"error": "Server error"})
        elif "gemini-fallback-2" in url_str:
            models_called.append("gemini-fallback-2")
            return httpx.Response(200, json=make_mock_gemini_response("Answered by fallback-2!"))
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-primary",
        fallback_models=["gemini-fallback-1", "gemini-fallback-2"],
        max_retries=1,  # 1 retry per model for fast test execution
        base_delay=0.05,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    resp = client.generate_content("Test multi fallback")
    assert resp.model == "gemini-fallback-2"
    assert resp.text == "Answered by fallback-2!"
    # primary tried 2 times (1 + 1 retry), fallback-1 tried 2 times, fallback-2 succeeded on 1st try
    assert models_called.count("gemini-primary") == 2
    assert models_called.count("gemini-fallback-1") == 2
    assert models_called.count("gemini-fallback-2") == 1


def test_gemini_all_models_fail_raises_request_error():
    """Verify GeminiRequestError is raised when all models and retries are exhausted."""
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "Quota exceeded"})

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        fallback_models=["gemini-2.0-flash"],
        max_retries=2,
        base_delay=0.05,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    with pytest.raises(GeminiRequestError) as exc_info:
        client.generate_content("Test doomed")

    assert "All configured Gemini models failed" in str(exc_info.value)


def test_gemini_missing_api_key_raises_config_error():
    """Verify GeminiConfigError is raised immediately if API key is missing."""
    client = GeminiClient(api_key="")
    with pytest.raises(GeminiConfigError) as exc_info:
        client.generate_content("Say hello")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


def test_gemini_embed_content():
    """Verify embed_content returns valid embedding vector."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert ":embedContent" in str(request.url)
        return httpx.Response(200, json=make_mock_embedding_response([0.5, 0.25, -0.1]))

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key="test-key-1234",
        model="gemini-2.5-flash",
        http_client=http_client,
    )

    resp = client.embed_content("Nightwatch SRE incident summary")
    assert isinstance(resp, GeminiEmbeddingResponse)
    assert resp.embedding == [0.5, 0.25, -0.1]
    assert resp.model == "text-embedding-004"


def test_gemini_logging_never_prints_secrets(caplog):
    """Verify secret API key is never logged during retries and fallbacks."""
    SECRET_KEY = "super-secret-gemini-key-9999"
    sleep_calls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "gemini-2.5-flash" in url_str:
            return httpx.Response(429, text=f"Quota exhausted for key {SECRET_KEY}")
        return httpx.Response(200, json=make_mock_gemini_response("Success"))

    transport = httpx.MockTransport(mock_handler)
    http_client = httpx.Client(transport=transport)

    client = GeminiClient(
        api_key=SECRET_KEY,
        model="gemini-2.5-flash",
        fallback_models=["gemini-2.0-flash"],
        max_retries=1,
        base_delay=0.01,
        http_client=http_client,
        sleep_fn=sleep_calls.append,
    )

    with caplog.at_level(logging.DEBUG):
        resp = client.generate_content("Check logs for leaks")
        assert resp.model == "gemini-2.0-flash"

    # Inspect all captured logs
    for record in caplog.records:
        assert SECRET_KEY not in record.message
        assert SECRET_KEY not in str(record.args)
