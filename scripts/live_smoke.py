"""Live check of the API client: one TTS call, then that WAV back through STT.

Usage: LOKUTOR_API_KEY=... python scripts/live_smoke.py
Loads api.py directly so Home Assistant does not need to be installed.
"""

import asyncio
import importlib.util
import os
import sys
import types
from pathlib import Path

import aiohttp

root = Path(__file__).resolve().parent.parent / "custom_components" / "lokutor"
pkg = types.ModuleType("lokutor")
pkg.__path__ = [str(root)]
sys.modules["lokutor"] = pkg
for name in ("const", "api"):
    spec = importlib.util.spec_from_file_location(f"lokutor.{name}", root / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"lokutor.{name}"] = mod
    spec.loader.exec_module(mod)
LokutorClient = sys.modules["lokutor.api"].LokutorClient


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = LokutorClient(session, os.environ["LOKUTOR_API_KEY"])
        await client.async_validate()
        print("validate: ok")
        wav = await client.async_synthesize("Hello from Lokutor.", "F1", "en", 1.0)
        assert wav[:4] == b"RIFF", "not a WAV"
        print(f"tts: {len(wav)} bytes, header {wav[:4]!r}")
        text = await client.async_transcribe(wav, "en")
        print(f"stt: {text!r}")
        assert "lokutor" in text.lower() or "hello" in text.lower()


asyncio.run(main())
