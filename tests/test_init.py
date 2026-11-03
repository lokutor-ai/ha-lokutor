"""Tests for the config flow and setup."""

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType

from custom_components.lokutor.const import DOMAIN

from .conftest import API


async def test_flow_creates_entry(hass, aioclient_mock):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", json={"dictionaries": []})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_key": " good-key "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"api_key": "good-key"}
    assert result["options"]["voice"] == "F1"
    assert aioclient_mock.mock_calls[0][3]["Authorization"] == "Bearer good-key"


async def test_flow_invalid_key(hass, aioclient_mock):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", status=401)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_key": "bad"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_flow_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", status=503)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_key": "k"}
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow(hass, aioclient_mock, entry):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", json={})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"voice": "M2", "language": "es", "speed": 1.2}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"voice": "M2", "language": "es", "speed": 1.2}


async def test_setup_and_unload(hass, aioclient_mock, entry):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", json={})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("tts.lokutor_text_to_speech") is not None
    assert hass.states.get("stt.lokutor_speech_to_text") is not None
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_bad_key_starts_reauth(hass, aioclient_mock, entry):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", status=401)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(hass.config_entries.flow.async_progress_by_handler(DOMAIN))


async def test_setup_unreachable_retries(hass, aioclient_mock, entry):
    aioclient_mock.get(f"{API}/pronunciation-dictionaries", status=500)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
