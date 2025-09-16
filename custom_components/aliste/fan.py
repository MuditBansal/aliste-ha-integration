from homeassistant.components.fan import FanEntity, FanEntityFeature
from .const import DOMAIN, APPLIANCE_FAN

SPEED_MAP = {"off": "0", "low": "25", "medium": "50", "high": "75", "max": "100"}

async def async_setup_entry(hass, entry, add_entities):
    store = hass.data[DOMAIN][entry.entry_id]
    coord = store["coordinator"]
    fans   = []

    for room in coord.data["rooms"]:
        for app in coord.data["devices"][room["_id"]]:
            if app["applianceType"] == APPLIANCE_FAN:
                fans.append(AlisteFan(store["api"], coord, room["_id"], app))
    add_entities(fans)

class AlisteFan(FanEntity):
    _attr_supported_features = FanEntityFeature.SET_SPEED
    _attr_speed_list = list(SPEED_MAP)

    def __init__(self, api, coord, room_id, app):
        self._api, self._coord = api, coord
        self._room_id, self._app = room_id, app
        self._attr_unique_id = f"{app['deviceId']}_{app['switchId']}"
        self._attr_name = app["name"]

    # -------------- SPEED --------------
    @property
    def percentage(self): return int(self._app["state"])

    async def async_set_speed(self, speed):
        cmd = SPEED_MAP.get(speed, "0")
        await self.hass.async_add_executor_job(self._api.action, self._app["deviceId"], self._app["switchId"], cmd)
        await self._coord.async_request_refresh()

    async def async_turn_on(self, **_):  await self.async_set_speed("max")
    async def async_turn_off(self, **_): await self.async_set_speed("off")

    # -------------- UPDATE --------------
    async def async_update(self):
        for a in self._coord.data["devices"][self._room_id]:
            if a["deviceId"] == self._app["deviceId"] and a["switchId"] == self._app["switchId"]:
                self._app = a
                break
