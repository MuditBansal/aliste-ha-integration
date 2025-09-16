from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, APPLIANCE_FAN

async def async_setup_entry(hass, entry, add_entities):
    store = hass.data[DOMAIN][entry.entry_id]
    coord = store["coordinator"]
    entities = []

    for room in coord.data["rooms"]:
        for app in coord.data["devices"][room["_id"]]:
            if app["applianceType"] != APPLIANCE_FAN:
                entities.append(AlisteSwitch(store["api"], coord, room["_id"], app))
    add_entities(entities)

class AlisteSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, api, coord, room_id, app):
        self._api, self._coord = api, coord
        self._room_id, self._app = room_id, app
        self._attr_unique_id = f"{app['deviceId']}_{app['switchId']}"
        self._attr_name = app["name"]

    @property
    def is_on(self): return int(self._app["state"]) > 0

    async def async_turn_on(self, **_):
        await self.hass.async_add_executor_job(self._api.action, self._app["deviceId"], self._app["switchId"], "100")
        await self._coord.async_request_refresh()

    async def async_turn_off(self, **_):
        await self.hass.async_add_executor_job(self._api.action, self._app["deviceId"], self._app["switchId"], "0")
        await self._coord.async_request_refresh()

    async def async_update(self):
        for a in self._coord.data["devices"][self._room_id]:
            if a["deviceId"] == self._app["deviceId"] and a["switchId"] == self._app["switchId"]:
                self._app = a
                break
