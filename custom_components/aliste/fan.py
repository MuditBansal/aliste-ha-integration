import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)
from .const import DOMAIN, APPLIANCE_FAN

# Define discrete speed steps: 0%, 25%, 50%, 75%, 100%
SPEED_RANGE = (1, 4)  # 4 speeds: low=1, medium=2, high=3, max=4
SPEED_TO_COMMAND = {0: "0", 1: "25", 2: "50", 3: "75", 4: "100"}
COMMAND_TO_SPEED = {"0": 0, "25": 1, "50": 2, "75": 3, "100": 4}

async def async_setup_entry(hass, entry, add_entities):
    store = hass.data[DOMAIN][entry.entry_id]
    coord = store["coordinator"]
    fans = []

    for room in coord.data["rooms"]:
        for app in coord.data["devices"][room["_id"]]:
            if app["applianceType"] == APPLIANCE_FAN:
                fans.append(AlisteFan(store["api"], coord, room["_id"], app))
    add_entities(fans)

class AlisteFan(CoordinatorEntity, FanEntity):
    _attr_supported_features = FanEntityFeature.SET_SPEED
    _attr_speed_count = 4  # 4 discrete speeds

    def __init__(self, api, coord, room_id, app):
        super().__init__(coord)
        self._api = api
        self._room_id = room_id
        self._device_id = app["deviceId"]
        self._switch_id = app["switchId"]
        self._attr_unique_id = f"{app['deviceId']}_{app['switchId']}"
        self._attr_name = app["name"]
        self._local_state = None

    def _get_current_appliance(self):
        """Get current appliance data from coordinator."""
        try:
            for app in self.coordinator.data["devices"][self._room_id]:
                if app["deviceId"] == self._device_id and app["switchId"] == self._switch_id:
                    return app
        except (KeyError, TypeError):
            pass
        return None

    @property
    def is_on(self):
        if self._local_state is not None:
            return self._local_state > 0
        
        current_app = self._get_current_appliance()
        return int(current_app["state"]) > 0 if current_app else False

    @property
    def percentage(self):
        """Return current speed as percentage."""
        if self._local_state is not None:
            speed_level = self._local_state
        else:
            current_app = self._get_current_appliance()
            if not current_app:
                return 0
            command_state = current_app["state"]
            speed_level = COMMAND_TO_SPEED.get(command_state, 0)
        
        if speed_level == 0:
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, speed_level)

    async def async_set_percentage(self, percentage: int):
        """Set fan speed by percentage - converts to discrete steps."""
        if percentage == 0:
            speed_level = 0
        else:
            # Convert percentage to discrete speed level
            speed_level = int(percentage_to_ranged_value(SPEED_RANGE, percentage))
        
        command = SPEED_TO_COMMAND[speed_level]
        
        # Set local state immediately
        self._local_state = speed_level
        self.async_write_ha_state()
        
        try:
            await self.hass.async_add_executor_job(
                self._api.action, self._device_id, str(self._switch_id), command
            )
            await asyncio.sleep(1.0)  # Give API time to update
            await self.coordinator.async_request_refresh()
            # Wait for confirmation via coordinator update
            await asyncio.sleep(0.5)
            self._local_state = None
            self.async_write_ha_state()
        except Exception:
            # Revert on error
            current_app = self._get_current_appliance()
            if current_app:
                self._local_state = COMMAND_TO_SPEED.get(current_app.get("state", "0"), 0)
            else:
                self._local_state = None
            self.async_write_ha_state()
            raise

    async def async_turn_on(self, percentage=None, **kwargs):
        """Turn on the fan with default speed 50% if not specified."""
        if percentage is None:
            percentage = 50
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
        """Turn off the fan by setting speed to 0%."""
        await self.async_set_percentage(0)

    def _handle_coordinator_update(self):
        """Handle coordinator update and clear local overrides if state matches."""
        if self._local_state is not None:
            current_app = self._get_current_appliance()
            if current_app:
                actual_speed = COMMAND_TO_SPEED.get(current_app.get("state", "0"), 0)
                if actual_speed == self._local_state:
                    self._local_state = None
        super()._handle_coordinator_update()
