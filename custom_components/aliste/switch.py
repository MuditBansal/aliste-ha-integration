import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
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

class AlisteSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, api, coord, room_id, app):
        super().__init__(coord)
        self._api = api
        self._room_id = room_id
        self._device_id = app["deviceId"]
        self._switch_id = app["switchId"]
        self._attr_unique_id = f"{app['deviceId']}_{app['switchId']}"
        self._attr_name = app["name"]
        # Track state locally to prevent toggle-back
        self._local_state = None
        self._pending_state = None

    @property
    def is_on(self):
        # Priority: pending_state > local_state > coordinator_data
        if self._pending_state is not None:
            return self._pending_state
        if self._local_state is not None:
            return self._local_state
        
        current_app = self._get_current_appliance()
        return int(current_app["state"]) > 0 if current_app else False

    def _get_current_appliance(self):
        """Get current appliance data from coordinator."""
        try:
            for app in self.coordinator.data["devices"][self._room_id]:
                if app["deviceId"] == self._device_id and app["switchId"] == self._switch_id:
                    return app
        except (KeyError, TypeError):
            pass
        return None

    async def async_turn_on(self, **_):
        # Set pending state immediately for instant UI feedback
        self._pending_state = True
        self.async_write_ha_state()
        
        try:
            # Execute the command
            result = await self.hass.async_add_executor_job(
                self._api.action, self._device_id, str(self._switch_id), "100"
            )
            
            # Check if API call was successful
            if result.get("success", False):
                self._local_state = True
                self._pending_state = None
                self.async_write_ha_state()
                
                # Wait for state to propagate, then refresh
                await asyncio.sleep(1.0)
                await self.coordinator.async_request_refresh()
                
                # Give coordinator time to update
                await asyncio.sleep(0.5)
                # Only clear local state if coordinator confirms the change
                current_app = self._get_current_appliance()
                if current_app and int(current_app["state"]) > 0:
                    self._local_state = None
                    self.async_write_ha_state()
            else:
                # API call failed, revert state
                self._pending_state = None
                self._local_state = False
                self.async_write_ha_state()
                
        except Exception as e:
            # Revert state on error
            self._pending_state = None
            self._local_state = False
            self.async_write_ha_state()
            raise e

    async def async_turn_off(self, **_):
        # Set pending state immediately for instant UI feedback
        self._pending_state = False
        self.async_write_ha_state()
        
        try:
            # Execute the command
            result = await self.hass.async_add_executor_job(
                self._api.action, self._device_id, str(self._switch_id), "0"
            )
            
            # Check if API call was successful
            if result.get("success", False):
                self._local_state = False
                self._pending_state = None
                self.async_write_ha_state()
                
                # Wait for state to propagate, then refresh
                await asyncio.sleep(1.0)
                await self.coordinator.async_request_refresh()
                
                # Give coordinator time to update
                await asyncio.sleep(0.5)
                # Only clear local state if coordinator confirms the change
                current_app = self._get_current_appliance()
                if current_app and int(current_app["state"]) == 0:
                    self._local_state = None
                    self.async_write_ha_state()
            else:
                # API call failed, revert state
                self._pending_state = None
                self._local_state = True
                self.async_write_ha_state()
                
        except Exception as e:
            # Revert state on error
            self._pending_state = None
            self._local_state = True
            self.async_write_ha_state()
            raise e

    def _handle_coordinator_update(self):
        """Handle coordinator update - only clear local state if it matches reality."""
        if self._local_state is not None and self._pending_state is None:
            current_app = self._get_current_appliance()
            if current_app:
                actual_state = int(current_app["state"]) > 0
                if actual_state == self._local_state:
                    # State confirmed by coordinator, clear local override
                    self._local_state = None
        super()._handle_coordinator_update()
