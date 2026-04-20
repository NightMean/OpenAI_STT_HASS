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
            if response.status >= 500:
                return {"error": "cannot_connect"}

            return {"title": "OpenAI STT"}
    except aiohttp.ClientError:
        return {"error": "cannot_connect"}
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        return {"error": "unknown"}


async def fetch_models(hass: HomeAssistant, api_key: str, api_url: str) -> list[str]:
    """Fetch available models from the server's /models endpoint."""
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
            if response.status != 200:
                return []

            data = await response.json()

            # OpenAI format: {"data": [{"id": "model-name", ...}, ...]}
            if isinstance(data, dict) and "data" in data:
                models = []
                for model in data["data"]:
                    if isinstance(model, dict) and "id" in model:
                        models.append(model["id"])
                return sorted(models)

            # Some servers return a flat list: ["model-1", "model-2"]
            if isinstance(data, list):
                models = []
                for item in data:
                    if isinstance(item, str):
                        models.append(item)
                    elif isinstance(item, dict) and "id" in item:
                        models.append(item["id"])
                return sorted(models)

            return []
    except Exception:
        _LOGGER.debug("Failed to fetch models from %s/models", api_url)
        return []


class OpenAISTTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenAI STT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_key: str = ""
        self._api_url: str = DEFAULT_API_URL
        self._name: str = "OpenAI STT"
        self._available_models: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step — connection details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._api_key = user_input.get(CONF_API_KEY, "")
            self._api_url = user_input.get(CONF_API_URL, DEFAULT_API_URL)
            self._name = user_input.get("name", "OpenAI STT")

            result = await validate_connection(self.hass, self._api_key, self._api_url)

            if "error" in result:
                errors["base"] = result["error"]
            else:
                self._available_models = await fetch_models(
                    self.hass, self._api_key, self._api_url
                )
                return await self.async_step_model()

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_API_KEY, default=""): str,
                vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Optional("name", default="OpenAI STT"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_model(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the model selection step."""
        if user_input is not None:
            model = user_input.get(CONF_MODEL, DEFAULT_MODEL)

            return self.async_create_entry(
                title=self._name,
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_API_URL: self._api_url,
                },
                options={
                    CONF_MODEL: model,
                    CONF_PROMPT: DEFAULT_PROMPT,
                    CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
                    CONF_REALTIME: DEFAULT_REALTIME,
                    CONF_NOISE_REDUCTION: DEFAULT_NOISE_REDUCTION,
                },
            )

        if self._available_models:
            default_model = (
                DEFAULT_MODEL if DEFAULT_MODEL in self._available_models
                else self._available_models[0]
            )
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=default_model): selector({
                        "select": {
                            "options": [
                                {"label": m, "value": m}
                                for m in self._available_models
                            ],
                            "mode": "dropdown",
                            "custom_value": True,
                        }
                    }),
                }
            )
        else:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=DEFAULT_MODEL): str,
                }
            )

        return self.async_show_form(
            step_id="model",
            data_schema=data_schema,
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
        config_data = self.config_entry.data

        # Try to fetch models for the dropdown
        available_models = await fetch_models(
            self.hass,
            config_data.get(CONF_API_KEY, ""),
            config_data.get(CONF_API_URL, DEFAULT_API_URL),
        )

        current_model = options.get(CONF_MODEL, DEFAULT_MODEL)

        if available_models:
            # Ensure current model is in the list even if server no longer reports it
            if current_model and current_model not in available_models:
                available_models = [current_model] + available_models

            model_selector = selector({
                "select": {
                    "options": [
                        {"label": m, "value": m}
                        for m in available_models
                    ],
                    "mode": "dropdown",
                    "custom_value": True,
                }
            })
        else:
            model_selector = selector({
                "text": {
                    "type": "text",
                }
            })

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
                    default=current_model,
                ): model_selector,
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
