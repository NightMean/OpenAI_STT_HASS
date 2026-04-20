"""Config flow for OpenAI STT integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import selector
import aiohttp

from .const import (
    CONF_API_URL,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_REALTIME,
    CONF_NOISE_REDUCTION,
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_REALTIME,
    DEFAULT_NOISE_REDUCTION,
    DOMAIN,
    NOISE_REDUCTION_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, api_key: str, api_url: str) -> dict[str, str]:
    """Validate the connection by making a test request."""
    session = async_get_clientsession(hass)

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with session.get(
            f"{api_url}/models",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == 401:
                return {"error": "invalid_auth"}
            # Accept any successful response (some servers return different codes)
            if response.status >= 500:
                return {"error": "cannot_connect"}

            return {"title": "OpenAI STT"}
    except aiohttp.ClientError:
        return {"error": "cannot_connect"}
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        return {"error": "unknown"}


class OpenAISTTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenAI STT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "")
            api_url = user_input.get(CONF_API_URL, DEFAULT_API_URL)
            name = user_input.get("name", "OpenAI STT")
            model = user_input.get(CONF_MODEL, DEFAULT_MODEL)

            result = await validate_connection(self.hass, api_key, api_url)

            if "error" in result:
                errors["base"] = result["error"]
            else:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_API_URL: api_url,
                    },
                    options={
                        CONF_MODEL: model,
                        CONF_PROMPT: DEFAULT_PROMPT,
                        CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
                        CONF_REALTIME: DEFAULT_REALTIME,
                        CONF_NOISE_REDUCTION: DEFAULT_NOISE_REDUCTION,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_API_KEY, default=""): str,
                vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
                vol.Optional("name", default="OpenAI STT"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OpenAISTTOptionsFlow:
        """Get the options flow for this handler."""
        return OpenAISTTOptionsFlow(config_entry)


class OpenAISTTOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    """Handle options flow for OpenAI STT."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            if "friendly_name" in user_input:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=user_input["friendly_name"]
                )
                user_input = {k: v for k, v in user_input.items() if k != "friendly_name"}

            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "friendly_name",
                    default=self.config_entry.title,
                ): selector({
                    "text": {
                        "type": "text",
                    }
                }),
                vol.Optional(
                    CONF_MODEL,
                    default=options.get(CONF_MODEL, DEFAULT_MODEL),
                ): selector({
                    "text": {
                        "type": "text",
                    }
                }),
                vol.Optional(
                    CONF_PROMPT,
                    default=options.get(CONF_PROMPT, DEFAULT_PROMPT),
                ): selector({
                    "text": {
                        "multiline": True,
                        "type": "text",
                    }
                }),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                vol.Optional(
                    CONF_REALTIME,
                    default=options.get(CONF_REALTIME, DEFAULT_REALTIME),
                ): bool,
                vol.Optional(
                    CONF_NOISE_REDUCTION,
                    default=options.get(CONF_NOISE_REDUCTION, DEFAULT_NOISE_REDUCTION),
                ): selector({
                    "select": {
                        "options": [
                            {"label": "None", "value": "none"},
                            {"label": "Near Field", "value": "near_field"},
                            {"label": "Far Field", "value": "far_field"},
                        ],
                        "mode": "dropdown",
                    }
                }),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
