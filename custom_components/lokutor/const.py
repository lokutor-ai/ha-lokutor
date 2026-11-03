"""Constants for the Lokutor integration."""

from __future__ import annotations

DOMAIN = "lokutor"

API_BASE_URL = "https://api.lokutor.com"
OPENAI_BASE_URL = f"{API_BASE_URL}/v1"

# The model name is accepted and ignored by the API (every request uses Versa 2.0).
MODEL = "versa-2.0"

CONF_VOICE = "voice"
CONF_LANGUAGE = "language"
CONF_SPEED = "speed"

DEFAULT_VOICE = "F1"
DEFAULT_LANGUAGE = "en"
DEFAULT_SPEED = 1.0
MIN_SPEED = 0.5
MAX_SPEED = 2.0

# Voice slots and their display names (https://api.lokutor.com/voices).
VOICES: dict[str, str] = {
    "F1": "Claire",
    "F2": "Sophie",
    "F3": "Emma",
    "F4": "Maria",
    "F5": "Isabella",
    "M1": "James",
    "M2": "Oliver",
    "M3": "Lucas",
    "M4": "Ethan",
    "M5": "Noah",
}

# Languages Lokutor speaks and recognises (the same nine, one model).
LANGUAGES: list[str] = ["en", "es", "ca", "gl", "eu", "pt", "fr", "it", "de"]
