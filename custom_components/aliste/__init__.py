from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import AlisteAPI
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aliste from a config entry."""
    # Store API client instance in hass.data for platforms to access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = AlisteAPI(
        entry.data["username"],
        entry.data["password"],
    )
    
    # Load platforms (switch, fan, etc.)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "fan")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Aliste config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "fan"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
