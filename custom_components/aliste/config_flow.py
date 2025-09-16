import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("key_id"): int,
    }
)

class AlisteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aliste integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]
            key_id = user_input["key_id"]

            # Here you could add a preliminary validation by trying to renew token or get houses
            # For brevity, assume success
            return self.async_create_entry(
                title=username,
                data={
                    "username": username,
                    "password": password,
                    "key_id": key_id,
                },
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        from .options_flow import AlisteOptionsFlow
        return AlisteOptionsFlow(config_entry)
