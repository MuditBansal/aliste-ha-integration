from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import AlisteAPI
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aliste from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = AlisteAPI(
        entry.data["username"],
        entry.data["password"],
    )

    # Forward setup to switch and fan platforms together
    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "fan"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Aliste config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "fan"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
