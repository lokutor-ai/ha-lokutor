"""Small async client for Lokutor's OpenAI-compatible audio API."""

from __future__ import annotations

import asyncio
import io
import wave
from typing import Any

import aiohttp

from .const import API_BASE_URL, MODEL, OPENAI_BASE_URL

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=60)


class LokutorError(Exception):
    """Base error for Lokutor API failures."""


class LokutorAuthError(LokutorError):
    """The API key was rejected."""


class LokutorConnectionError(LokutorError):
    """The API could not be reached."""


def pcm_to_wav(pcm: bytes, sample_rate: int, channels: int, sample_width: int) -> bytes:
    """Wrap raw PCM samples in a WAV container."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return buffer.getvalue()


class LokutorClient:
    """Client for the Lokutor speech API."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._headers = {"Authorization": f"Bearer {api_key}"}

    async def _request(self, method: str, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        try:
            response = await self._session.request(
                method,
                url,
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise LokutorConnectionError(str(err)) from err
        if response.status in (401, 403):
            response.release()
            raise LokutorAuthError("Invalid API key")
        if response.status >= 400:
            try:
                detail = (await response.text())[:300]
            finally:
                response.release()
            raise LokutorError(f"HTTP {response.status}: {detail}")
        return response

    async def async_validate(self) -> None:
        """Check the key against a free authenticated endpoint (no audio billed)."""
        response = await self._request("GET", f"{API_BASE_URL}/pronunciation-dictionaries")
        response.release()

    async def async_synthesize(
        self,
        text: str,
        voice: str,
        language: str | None = None,
        speed: float | None = None,
    ) -> bytes:
        """Return a WAV clip speaking the text."""
        payload: dict[str, Any] = {"model": MODEL, "input": text, "voice": voice}
        if language:
            payload["language"] = language
        if speed is not None:
            payload["speed"] = speed
        response = await self._request(
            "POST", f"{OPENAI_BASE_URL}/audio/speech", json=payload
        )
        try:
            return await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise LokutorConnectionError(str(err)) from err
        finally:
            response.release()

    async def async_transcribe(self, wav: bytes, language: str | None = None) -> str:
        """Return the text spoken in a WAV clip."""
        form = aiohttp.FormData()
        form.add_field("file", wav, filename="audio.wav", content_type="audio/wav")
        form.add_field("model", "whisper-1")
        form.add_field("response_format", "json")
        if language:
            form.add_field("language", language)
        response = await self._request(
            "POST", f"{OPENAI_BASE_URL}/audio/transcriptions", data=form
        )
        try:
            data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise LokutorError(f"Unreadable transcription response: {err}") from err
        finally:
            response.release()
        return str(data.get("text", "")).strip()
