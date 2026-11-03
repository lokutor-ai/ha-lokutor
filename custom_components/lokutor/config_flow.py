"""Config flow for Lokutor."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import LokutorAuthError, LokutorClient, LokutorError
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

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        )
    }
)


async def _validate(flow: ConfigFlow, api_key: str) -> str | None:
    """Return an error key if the key does not work, else None."""
    client = LokutorClient(async_get_clientsession(flow.hass), api_key)
    try:
        await client.async_validate()
    except LokutorAuthError:
        return "invalid_auth"
    except LokutorError:
        return "cannot_connect"
    return None


class LokutorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lokutor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            self._async_abort_entries_match({CONF_API_KEY: api_key})
            if error := await _validate(self, api_key):
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title="Lokutor",
                    data={CONF_API_KEY: api_key},
                    options={
                        CONF_VOICE: DEFAULT_VOICE,
                        CONF_LANGUAGE: DEFAULT_LANGUAGE,
                        CONF_SPEED: DEFAULT_SPEED,
                    },
                )
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication after a rejected key."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            if error := await _validate(self, api_key):
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates={CONF_API_KEY: api_key}
                )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return LokutorOptionsFlow()


class LokutorOptionsFlow(OptionsFlow):
    """Voice, language and speed options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_VOICE, default=options.get(CONF_VOICE, DEFAULT_VOICE)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=slot, label=f"{slot} ({name})")
                            for slot, name in VOICES.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_LANGUAGE, default=options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=LANGUAGES,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="language",
                    )
                ),
                vol.Required(
                    CONF_SPEED, default=options.get(CONF_SPEED, DEFAULT_SPEED)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SPEED,
                        max=MAX_SPEED,
                        step=0.05,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
