"""Lokutor speech-to-text platform."""

from __future__ import annotations

from collections.abc import AsyncIterable
import logging

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LokutorConfigEntry
from .api import LokutorClient, LokutorError, pcm_to_wav
from .const import DOMAIN, LANGUAGES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LokutorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Lokutor STT entity."""
    async_add_entities([LokutorSTTEntity(entry)])


class LokutorSTTEntity(SpeechToTextEntity):
    """Lokutor speech-to-text (one-shot transcription of a finished utterance)."""

    _attr_has_entity_name = True
    _attr_name = "Speech-to-text"

    def __init__(self, entry: LokutorConfigEntry) -> None:
        """Initialize the entity."""
        self._client: LokutorClient = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}-stt"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Lokutor",
            model="Versa 2.0",
            name="Lokutor",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def supported_languages(self) -> list[str]:
        """Return the recognised languages."""
        return LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """The API takes WAV (Home Assistant streams raw PCM, wrapped here)."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return the supported codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return the supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return the supported sample rates."""
        return [
            AudioSampleRates.SAMPLERATE_8000,
            AudioSampleRates.SAMPLERATE_16000,
            AudioSampleRates.SAMPLERATE_22000,
            AudioSampleRates.SAMPLERATE_44100,
            AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return the supported channel layouts."""
        return [AudioChannels.CHANNEL_MONO, AudioChannels.CHANNEL_STEREO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Transcribe the whole utterance."""
        pcm = bytearray()
        async for chunk in stream:
            pcm.extend(chunk)
        if not pcm:
            return SpeechResult(None, SpeechResultState.ERROR)

        wav = pcm_to_wav(
            bytes(pcm),
            int(metadata.sample_rate),
            int(metadata.channel),
            int(metadata.bit_rate) // 8,
        )
        language = metadata.language.split("-")[0].lower()
        try:
            text = await self._client.async_transcribe(
                wav, language if language in LANGUAGES else None
            )
        except LokutorError as err:
            _LOGGER.error("Lokutor speech-to-text failed: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)
        if not text:
            return SpeechResult(None, SpeechResultState.ERROR)
        return SpeechResult(text, SpeechResultState.SUCCESS)
