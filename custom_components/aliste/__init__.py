from datetime import timedelta
import logging, asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import AlisteAPI
from .const import DOMAIN, UPDATE_INTERVAL

_LOG = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Aliste integration."""
    cred = entry.options or entry.data
    api  = AlisteAPI(cred["username"], cred["password"])

    async def _refresh():
        try:
            houses   = await hass.async_add_executor_job(api.houses)
            house_id = houses["data"]["houses"][0]["_id"]
            rooms    = await hass.async_add_executor_job(api.rooms, house_id)
            devices  = {}
            for r in rooms["data"]["rooms"]:
                apps = await hass.async_add_executor_job(api.appliances, r["_id"])
                devices[r["_id"]] = apps["data"]["appliancesData"]
            return {"house": house_id, "rooms": rooms["data"]["rooms"], "devices": devices}
        except Exception as err:
            raise UpdateFailed(err)

    coord = DataUpdateCoordinator(
        hass, _LOG, name="aliste_coordinator",
        update_method=_refresh,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )
    await coord.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"api": api, "coordinator": coord}

    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "fan"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(entry, ["switch", "fan"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
