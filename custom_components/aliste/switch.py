import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import AlisteAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    """Set up Aliste switches."""
    api = hass.data[DOMAIN][entry.entry_id]

    # Use executor job for blocking API calls
    houses = await hass.async_add_executor_job(api.get_house_id)
    if not houses or "houses" not in houses or not houses["houses"]:
        _LOGGER.error("No houses found for the user")
        return

    house_id = houses["houses"]["houseId"]

    # Fetch rooms using executor job
    rooms_resp = await hass.async_add_executor_job(api.get_rooms, house_id)
    rooms = rooms_resp.get("rooms", [])

    switches = []

    for room in rooms:
        room_id = room["roomId"]
        appliances_resp = await hass.async_add_executor_job(api.get_appliances, room_id)
        appliances = appliances_resp.get("data", {}).get("appliancesData", [])

        for appliance in appliances:
            appliance_type = appliance.get("applianceType")
            if appliance_type != 20:  # Not fan type
                switches.append(AlisteSwitch(api, appliance, room))

    async_add_entities(switches, update_before_add=True)


class AlisteSwitch(SwitchEntity):
    def __init__(self, api: AlisteAPI, appliance: dict, room: dict):
        self._api = api
        self._appliance = appliance
        self._room = room
        self._is_on = int(appliance.get("state", "0")) > 0
        self._attr_name = appliance.get("name", "Aliste Switch")
        self._unique_id = f"aliste_switch_{appliance.get('deviceId')}_{appliance.get('switchId')}"

    @property
    def is_on(self):
        return self._is_on

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(
            self._api.execute_action,
            self._appliance["deviceId"],
            str(self._appliance["switchId"]),
            "100"
        )
        self._is_on = True
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(
            self._api.execute_action,
            self._appliance["deviceId"],
            str(self._appliance["switchId"]),
            "0"
        )
        self._is_on = False
        self.schedule_update_ha_state()

    async def async_update(self):
        """Fetch latest state from API using executor."""
        appliances_resp = await self.hass.async_add_executor_job(
            self._api.get_appliances, 
            self._room["roomId"]
        )
        appliances = appliances_resp.get("data", {}).get("appliancesData", [])
        for appl in appliances:
            if (
                appl["deviceId"] == self._appliance["deviceId"]
                and appl["switchId"] == self._appliance["switchId"]
            ):
                self._is_on = int(appl.get("state", "0")) > 0
                break
