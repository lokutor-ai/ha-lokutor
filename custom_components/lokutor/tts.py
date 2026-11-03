"""Lokutor text-to-speech platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LokutorConfigEntry
from .api import LokutorClient, LokutorError
from .const import (
    CONF_LANGUAGE,
    CONF_SPEED,
    CONF_VOICE,
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
    DOMAIN,
    LANGUAGES,
    MAX_SPEED,
    MIN_SPEED,
    VOICES,
)

_LOGGER = logging.getLogger(__name__)

ATTR_SPEED = "speed"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LokutorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Lokutor TTS entity."""
    async_add_entities([LokutorTTSEntity(entry)])


class LokutorTTSEntity(TextToSpeechEntity):
    """Lokutor text-to-speech."""

    _attr_has_entity_name = True
    _attr_name = "Text-to-speech"
    _attr_supported_languages = LANGUAGES
    _attr_supported_options = [ATTR_VOICE, ATTR_SPEED]
    _attr_default_options = {ATTR_VOICE: DEFAULT_VOICE, ATTR_SPEED: DEFAULT_SPEED}

    def __init__(self, entry: LokutorConfigEntry) -> None:
        """Initialize the entity."""
        self._client: LokutorClient = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}-tts"
        self._attr_default_language = entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        self._attr_default_options = {
            ATTR_VOICE: entry.options.get(CONF_VOICE, DEFAULT_VOICE),
            ATTR_SPEED: entry.options.get(CONF_SPEED, DEFAULT_SPEED),
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Lokutor",
            model="Versa 2.0",
            name="Lokutor",
            entry_type=DeviceEntryType.SERVICE,
        )

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        """Return the ten voice slots (each speaks every supported language)."""
        return [Voice(slot, f"{name} ({slot})") for slot, name in VOICES.items()]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Synthesize a WAV clip."""
        voice = options.get(ATTR_VOICE, self._attr_default_options[ATTR_VOICE])
        if voice not in VOICES:
            # Other ids (an OpenAI voice name or a cloned voice) pass through.
            _LOGGER.debug("Using non-slot voice %s", voice)
        try:
            speed = float(options.get(ATTR_SPEED, self._attr_default_options[ATTR_SPEED]))
        except (TypeError, ValueError):
            speed = DEFAULT_SPEED
        speed = min(max(speed, MIN_SPEED), MAX_SPEED)
        lang = language.split("-")[0].lower() if language else None
        try:
            audio = await self._client.async_synthesize(
                message, voice, lang if lang in LANGUAGES else None, speed
            )
        except LokutorError as err:
            _LOGGER.error("Lokutor text-to-speech failed: %s", err)
            raise HomeAssistantError("Lokutor text-to-speech failed") from err
        return "wav", audio
