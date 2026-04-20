"""Custom integration for OpenAI Whisper STT API."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.STT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI STT from a config entry."""
    try:
        _LOGGER.debug("Setting up OpenAI STT integration for entry: %s", entry.entry_id)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = entry.data | entry.options

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info("OpenAI STT integration setup completed for entry: %s", entry.entry_id)
        return True
    except Exception as err:
        _LOGGER.exception("Failed to set up OpenAI STT integration: %s", err)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
