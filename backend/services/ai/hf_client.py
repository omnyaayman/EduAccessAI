"""Centralized Hugging Face Client for EduAccess AI.

Provides a robust, centralized gateway to Hugging Face Cloud Inference:
- Secure authentication (HF_TOKEN read from config, never logged or exposed)
- Model routing (Serverless Inference API / router.huggingface.co / dedicated endpoints)
- Timeouts, retries with exponential backoff (handling 503 model loading & 429 rate limits)
- Request logging without credential leakage
- Structured response parsing and error classification
"""
from __future__ import annotations

import json
import logging
import asyncio
import time
from typing import Any, AsyncGenerator
import httpx

from backend import config

logger = logging.getLogger("eduaccess.ai.hf")

HF_ROUTER_BASE = "https://router.huggingface.co/hf-inference/models"
HF_INFERENCE_BASE = "https://api-inference.huggingface.co/models"
HF_CHAT_COMPLETIONS_URL = "https://router.huggingface.co/v1/chat/completions"


class HFClientError(Exception):
    """Custom exception for Hugging Face Cloud interactions."""
    def __init__(self, message: str, status_code: int | None = None, is_auth_error: bool = False, is_loading: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.is_auth_error = is_auth_error
        self.is_loading = is_loading


class HFClient:
    """Centralized client for Hugging Face inference APIs."""

    def __init__(self, token: str | None = None, timeout: float = 45.0, max_retries: int = 3):
        # An explicit empty string is useful for offline tests and disables
        # configuration rather than unexpectedly inheriting the environment.
        self.token = config.HF_TOKEN if token is None else token
        self.timeout = timeout
        self.max_retries = max_retries
        # One client per gateway instance keeps TCP/TLS connections alive across
        # requests.  Model weights are never fetched by this client.
        self._sync_client = httpx.Client(timeout=timeout)
        self._async_client = httpx.AsyncClient(timeout=timeout)

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def _resolve_url(self, model_id: str, endpoint_override: str | None = None) -> str:
        if endpoint_override and endpoint_override.strip():
            return endpoint_override.strip().rstrip("/")
        clean_model = model_id.strip().lstrip("/")
        return f"{HF_ROUTER_BASE}/{clean_model}"

    def post_sync(
        self,
        model_id: str,
        payload: dict[str, Any] | bytes,
        endpoint_override: str | None = None,
        timeout: float | None = None,
        is_binary: bool = False,
    ) -> Any:
        """Synchronous HTTP POST to Hugging Face model with retry & backoff."""
        if not self.is_configured:
            raise HFClientError("Hugging Face API token (HF_TOKEN) is not configured.", status_code=401, is_auth_error=True)

        url = self._resolve_url(model_id, endpoint_override)
        headers = self._get_headers()
        if is_binary:
            headers["Content-Type"] = "application/octet-stream"

        req_timeout = timeout or self.timeout
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if is_binary:
                    resp = self._sync_client.post(url, headers=headers, content=payload, timeout=req_timeout)
                else:
                    resp = self._sync_client.post(url, headers=headers, json=payload, timeout=req_timeout)

                if resp.status_code == 200:
                    if "application/json" in resp.headers.get("content-type", ""):
                        return resp.json()
                    return resp.content

                # Handle model loading (503)
                if resp.status_code == 503:
                    try:
                        detail = resp.json()
                        estimated = detail.get("estimated_time", 5.0)
                    except Exception:
                        estimated = 5.0
                    wait_sec = min(float(estimated), 15.0)
                    logger.info(f"Model {model_id} loading. Waiting {wait_sec}s (attempt {attempt + 1}/{self.max_retries})...")
                    time.sleep(wait_sec)
                    continue

                # Handle rate limiting (429)
                if resp.status_code == 429:
                    wait_sec = (2 ** attempt) * 2.0
                    logger.warning(f"HF Rate limit hit for {model_id}. Backing off {wait_sec}s...")
                    time.sleep(wait_sec)
                    continue

                if resp.status_code in (401, 403):
                    raise HFClientError(f"Authentication failure on Hugging Face (HTTP {resp.status_code}). Check HF_TOKEN.", status_code=resp.status_code, is_auth_error=True)

                raise HFClientError(f"Hugging Face request failed with HTTP {resp.status_code}: {resp.text[:300]}", status_code=resp.status_code)

            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait_sec = (2 ** attempt) * 1.5
                    logger.warning(f"Network error calling HF ({exc}). Retrying in {wait_sec}s...")
                    time.sleep(wait_sec)
                else:
                    raise HFClientError(f"Connection to Hugging Face failed after {self.max_retries} retries: {exc}") from exc

        if last_error:
            raise HFClientError(f"HF request failed: {last_error}")

    async def post_async(
        self,
        model_id: str,
        payload: dict[str, Any] | bytes,
        endpoint_override: str | None = None,
        timeout: float | None = None,
        is_binary: bool = False,
    ) -> Any:
        """Asynchronous HTTP POST to Hugging Face model with retry & backoff."""
        if not self.is_configured:
            raise HFClientError("Hugging Face API token (HF_TOKEN) is not configured.", status_code=401, is_auth_error=True)

        url = self._resolve_url(model_id, endpoint_override)
        headers = self._get_headers()
        if is_binary:
            headers["Content-Type"] = "application/octet-stream"

        req_timeout = timeout or self.timeout
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if is_binary:
                    resp = await self._async_client.post(url, headers=headers, content=payload, timeout=req_timeout)
                else:
                    resp = await self._async_client.post(url, headers=headers, json=payload, timeout=req_timeout)

                if resp.status_code == 200:
                    if "application/json" in resp.headers.get("content-type", ""):
                        return resp.json()
                    return resp.content

                if resp.status_code == 503:
                    try:
                        detail = resp.json()
                        estimated = detail.get("estimated_time", 5.0)
                    except Exception:
                        estimated = 5.0
                    wait_sec = min(float(estimated), 15.0)
                    logger.info(f"Model {model_id} loading. Waiting {wait_sec}s...")
                    await asyncio.sleep(wait_sec)
                    continue

                if resp.status_code == 429:
                    wait_sec = (2 ** attempt) * 2.0
                    await asyncio.sleep(wait_sec)
                    continue

                if resp.status_code in (401, 403):
                    raise HFClientError(f"Authentication failure on Hugging Face (HTTP {resp.status_code}).", status_code=resp.status_code, is_auth_error=True)

                raise HFClientError(f"Hugging Face request failed: HTTP {resp.status_code} - {resp.text[:300]}", status_code=resp.status_code)

            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep((2 ** attempt) * 1.5)
                else:
                    raise HFClientError(f"Connection to Hugging Face failed: {exc}") from exc

        if last_error:
            raise HFClientError(f"HF request failed: {last_error}")

    async def stream_text_async(
        self,
        model_id: str,
        payload: dict[str, Any],
        endpoint_override: str | None = None,
        timeout: float = 60.0,
    ) -> AsyncGenerator[str, None]:
        """Stream SSE text generation tokens from Hugging Face Cloud."""
        if not self.is_configured:
            raise HFClientError("Hugging Face API token (HF_TOKEN) is not configured.", status_code=401, is_auth_error=True)

        url = self._resolve_url(model_id, endpoint_override)
        headers = self._get_headers()
        payload = {**payload, "stream": True}

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with self._async_client.stream("POST", url, headers=headers, json=payload, timeout=timeout) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data:"):
                                raw_data = line[5:].strip()
                                if raw_data == "[DONE]":
                                    break
                                try:
                                    parsed = json.loads(raw_data)
                                    token_text = ""
                                    if isinstance(parsed, dict):
                                        # Hugging Face's OpenAI-compatible chat endpoint
                                        # streams text in ``choices[].delta.content``.  Its
                                        # text-generation endpoints use ``token.text``;
                                        # support both formats so callers always receive
                                        # the generated response.
                                        choices = parsed.get("choices", [])
                                        if choices and isinstance(choices[0], dict):
                                            delta = choices[0].get("delta", {})
                                            if isinstance(delta, dict):
                                                token_text = str(delta.get("content", "") or "")
                                            if not token_text:
                                                message = choices[0].get("message", {})
                                                if isinstance(message, dict):
                                                    token_text = str(message.get("content", "") or "")
                                        if not token_text:
                                            token = parsed.get("token", {})
                                            token_text = (
                                                token.get("text", "") if isinstance(token, dict) else ""
                                            ) or parsed.get("generated_text", "")
                                    elif isinstance(parsed, list) and parsed:
                                        token_text = parsed[0].get("token", {}).get("text", "") or parsed[0].get("generated_text", "")
                                    if token_text:
                                        yield token_text
                                except Exception:
                                    yield raw_data
                        return

                    body = await response.aread()
                    body_text = body.decode(errors="ignore")[:300]

                    if response.status_code == 503:
                        try:
                            detail = json.loads(body_text)
                            estimated = detail.get("estimated_time", 5.0)
                        except Exception:
                            estimated = 5.0
                        wait_sec = min(float(estimated), 15.0)
                        logger.info(f"Model {model_id} loading for streaming. Waiting {wait_sec}s (attempt {attempt + 1}/{self.max_retries})...")
                        await asyncio.sleep(wait_sec)
                        continue

                    if response.status_code == 429:
                        wait_sec = (2 ** attempt) * 2.0
                        logger.warning(f"HF Rate limit hit for streaming {model_id}. Backing off {wait_sec}s (attempt {attempt + 1}/{self.max_retries})...")
                        await asyncio.sleep(wait_sec)
                        continue

                    if response.status_code in (401, 403):
                        raise HFClientError(f"Authentication failure on Hugging Face (HTTP {response.status_code}). Check HF_TOKEN.", status_code=response.status_code, is_auth_error=True)

                    raise HFClientError(f"Streaming failed with HTTP {response.status_code}: {body_text}", status_code=response.status_code)

            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait_sec = (2 ** attempt) * 1.5
                    logger.warning(f"Network error streaming HF ({exc}). Retrying in {wait_sec}s...")
                    await asyncio.sleep(wait_sec)
                else:
                    raise HFClientError(f"Connection to Hugging Face streaming failed after {self.max_retries} retries: {exc}") from exc

        if last_error:
            raise HFClientError(f"HF streaming failed: {last_error}")
        raise HFClientError(f"Streaming failed after {self.max_retries} retries.")

    def close(self) -> None:
        """Release the shared synchronous connection pool."""
        self._sync_client.close()

    async def aclose(self) -> None:
        """Release both connection pools during application shutdown."""
        self._sync_client.close()
        await self._async_client.aclose()


# Global shared client instance
_client_instance: HFClient | None = None

def get_hf_client() -> HFClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = HFClient()
    return _client_instance
