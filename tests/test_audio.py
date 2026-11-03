"""Tests for the TTS and STT entities."""

import io
import json
import wave

import pytest
from homeassistant.components import stt, tts
from homeassistant.exceptions import HomeAssistantError

from custom_components.lokutor.api import pcm_to_wav

from .conftest import API

TTS_ENTITY = "tts.lokutor_text_to_speech"
STT_ENTITY = "stt.lokutor_speech_to_text"


@pytest.fixture
async def setup(hass, aioclient_mock, entry):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", json={})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return aioclient_mock


def _body(mock):
    call = mock.mock_calls[-1]
    return call[2] if isinstance(call[2], dict) else json.loads(call[2])


async def test_tts_request_and_audio(hass, setup):
    wav = pcm_to_wav(b"\x00\x00" * 160, 16000, 1, 2)
    setup.post(f"{API}/v1/audio/speech", content=wav)
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    fmt, audio = await entity.async_get_tts_audio("Hola", "es-ES", {"voice": "M2", "speed": 1.25})
    assert (fmt, audio) == ("wav", wav)
    sent = _body(setup)
    assert sent == {
        "model": "versa-2.0", "input": "Hola", "voice": "M2",
        "language": "es", "speed": 1.25,
    }


async def test_tts_defaults_and_speed_clamp(hass, setup):
    setup.post(f"{API}/v1/audio/speech", content=b"RIFF")
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    await entity.async_get_tts_audio("Hi", "en", {"speed": 9})
    sent = _body(setup)
    assert sent["voice"] == "F1" and sent["speed"] == 2.0 and sent["language"] == "en"


async def test_tts_lists_voices_and_languages(hass, setup):
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    assert len(entity.async_get_supported_voices("en")) == 10
    assert entity.supported_languages == ["en", "es", "ca", "gl", "eu", "pt", "fr", "it", "de"]


async def test_tts_error_raises(hass, setup):
    setup.post(f"{API}/v1/audio/speech", status=402, text="insufficient balance")
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    with pytest.raises(HomeAssistantError):
        await entity.async_get_tts_audio("Hi", "en", {})


def _metadata(language="es-ES"):
    return stt.SpeechMetadata(
        language=language,
        format=stt.AudioFormats.WAV,
        codec=stt.AudioCodecs.PCM,
        bit_rate=stt.AudioBitRates.BITRATE_16,
        sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
        channel=stt.AudioChannels.CHANNEL_MONO,
    )


async def _stream(*chunks):
    for c in chunks:
        yield c


async def test_stt_wraps_pcm_and_returns_text(hass, setup):
    setup.post(f"{API}/v1/audio/transcriptions", json={"text": " hola mundo "})
    entity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    result = await entity.async_process_audio_stream(
        _metadata(), _stream(b"\x01\x00" * 100, b"\x02\x00" * 100)
    )
    assert result.result is stt.SpeechResultState.SUCCESS
    assert result.text == "hola mundo"
    form = setup.mock_calls[-1][2]
    fields = {f[0]["name"]: f for f in form._fields}
    assert fields["language"][2] == "es"
    with wave.open(io.BytesIO(fields["file"][2])) as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (16000, 1, 2)
        assert w.getnframes() == 200


async def test_stt_empty_and_error(hass, setup):
    entity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    result = await entity.async_process_audio_stream(_metadata(), _stream())
    assert result.result is stt.SpeechResultState.ERROR
    setup.post(f"{API}/v1/audio/transcriptions", status=500)
    result = await entity.async_process_audio_stream(_metadata(), _stream(b"\x00\x00" * 10))
    assert result.result is stt.SpeechResultState.ERROR
