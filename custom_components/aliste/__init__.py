from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import AlisteAPI
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    cred = entry.options or entry.data
    api = AlisteAPI(cred["username"], cred["password"])

    async def _refresh():
        try:
            try:
                houses = await hass.async_add_executor_job(api.houses)
            except Exception as ex:
                raise UpdateFailed(f"Network or API error getting houses: {ex}")
            houses_data = houses.get("data", {})
            house_list = houses_data.get("houses", [])
            if not house_list:
                raise UpdateFailed(f"No houses found: {houses}")
            house_id = house_list[0].get("_id")
            if not house_id:
                raise UpdateFailed(f"House ID missing: {house_list}")

            try:
                rooms = await hass.async_add_executor_job(api.rooms, house_id)
            except Exception as ex:
                raise UpdateFailed(f"Network or API error getting rooms: {ex}")
            rooms_data = rooms.get("data", {})
            room_list = rooms_data.get("rooms", [])
            if not room_list:
                raise UpdateFailed(f"No rooms found: {rooms}")

            devices = {}
            for r in room_list:
                try:
                    apps = await hass.async_add_executor_job(api.appliances, r.get("_id"))
                except Exception as ex:
                    _LOGGER.error(f"Error fetching appliances for room {r.get('roomName', r.get('_id'))}: {ex}")
                    continue
                app_data = apps.get("data", {})
                app_list = app_data.get("appliancesData", [])
                if not app_list:
                    _LOGGER.error(f"Room {r.get('roomName', r.get('_id'))} has empty appliances: {apps}")
                    continue
                devices[r["_id"]] = app_list
            return {"house": house_id, "rooms": room_list, "devices": devices}
        except Exception as err:
            _LOGGER.error(f"Coordinator refresh failed: {err}")
            raise UpdateFailed(str(err))

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="aliste_coordinator",
        update_method=_refresh,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"api": api, "coordinator": coordinator}
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "fan"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(entry, ["switch", "fan"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)
