import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.fan import FanEntity, SUPPORT_SET_SPEED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from typing import List

from .api import AlisteAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities: AddEntitiesCallback, discovery_info=None):
    """Set up the Aliste switches and fans."""
    username = config.get("username")
    password = config.get("password")
    key_id = config.get("key_id")  # If needed for token renew (could be passed to API wrapper)
    
    api = AlisteAPI(username, password)
    
    # Fetch houses - assume first house for now
    houses = api.get_house_id()
    if not houses or "houses" not in houses or not houses["houses"]:
        _LOGGER.error("No houses found for the user")
        return
    
    house_id = houses["houses"][0]["houseId"]
    
    # Fetch rooms
    rooms_resp = api.get_rooms(house_id)
    rooms = rooms_resp.get("rooms", [])
    
    entities: List = []
    
    for room in rooms:
        room_id = room["roomId"]
        appliances_resp = api.get_appliances(room_id)
        appliances = appliances_resp.get("data", {}).get("appliancesData", [])
        
        for appliance in appliances:
            appliance_type = appliance.get("applianceType")
            # Fan applianceType assumed to be 20; lights and others treated as switches
            if appliance_type == 20:
                entities.append(AlisteFan(api, appliance, room))
            else:
                entities.append(AlisteSwitch(api, appliance, room))
    
    async_add_entities(entities, update_before_add=True)


class AlisteSwitch(SwitchEntity):
    """Representation of a simple ON/OFF Aliste switch device."""

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
        """Fetch latest state from API."""
        appliances_resp = self._api.get_appliances(self._room["roomId"])
        appliances = appliances_resp.get("data", {}).get("appliancesData", [])
        for appl in appliances:
            if (
                appl["deviceId"] == self._appliance["deviceId"]
                and appl["switchId"] == self._appliance["switchId"]
            ):
                self._is_on = int(appl.get("state", "0")) > 0
                break


class AlisteFan(FanEntity):
    """Representation of an Aliste fan with speed control."""

    def __init__(self, api: AlisteAPI, appliance: dict, room: dict):
        self._api = api
        self._appliance = appliance
        self._room = room
        self._speed = int(appliance.get("state", "0"))
        self._attr_name = appliance.get("name", "Aliste Fan")
        self._unique_id = f"aliste_fan_{appliance.get('deviceId')}_{appliance.get('switchId')}"
    
    @property
    def unique_id(self):
        return self._unique_id
    
    @property
    def name(self):
        return self._attr_name
    
    @property
    def speed(self):
        """Return the current speed level as a string key from speed_list."""
        # Map percentage to speed label
        speed_percent = self._speed
        if speed_percent == 0:
            return "off"
        elif speed_percent <= 25:
            return "low"
        elif speed_percent <= 50:
            return "medium"
        elif speed_percent <= 75:
            return "high"
        else:
            return "max"
    
    @property
    def speed_list(self):
        return ["off", "low", "medium", "high", "max"]
    
    @property
    def supported_features(self):
        return SUPPORT_SET_SPEED
    
    async def async_turn_on(self, **kwargs):
        # Turn on with max speed if no speed provided
        await self.async_set_speed("max")
    
    async def async_turn_off(self, **kwargs):
        await self.async_set_speed("off")
    
    async def async_set_speed(self, speed):
        # Map speed name to command value expected by API
        speed_map = {
            "off": "0",
            "low": "25",
            "medium": "50",
            "high": "75",
            "max": "100",
        }
        command_value = speed_map.get(speed, "0")
        await self.hass.async_add_executor_job(
            self._api.execute_action,
            self._appliance["deviceId"],
            str(self._appliance["switchId"]),
            command_value,
        )
        self._speed = int(command_value)
        self.schedule_update_ha_state()
    
    async def async_update(self):
        """Fetch latest state from API."""
        appliances_resp = self._api.get_appliances(self._room["roomId"])
        appliances = appliances_resp.get("data", {}).get("appliancesData", [])
        for appl in appliances:
            if (
                appl["deviceId"] == self._appliance["deviceId"]
                and appl["switchId"] == self._appliance["switchId"]
            ):
                self._speed = int(appl.get("state", "0"))
                break
