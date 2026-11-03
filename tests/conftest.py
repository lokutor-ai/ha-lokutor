"""Fixtures for the Lokutor tests."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lokutor.const import DOMAIN

API = "https://api.lokutor.com"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components."""
    yield


@pytest.fixture
def entry(hass):
    """A config entry with default options."""
    e = MockConfigEntry(
        domain=DOMAIN,
        data={"api_key": "test-key"},
        options={"voice": "F1", "language": "en", "speed": 1.0},
        unique_id=None,
    )
    e.add_to_hass(hass)
    return e
