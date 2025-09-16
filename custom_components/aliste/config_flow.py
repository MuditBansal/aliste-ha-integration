import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)

class AlisteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aliste integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            # Optionally could validate credentials here
            return self.async_create_entry(
                title=user_input["username"],
                data={
                    "username": user_input["username"],
                    "password": user_input["password"],
                },
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    # Removed async_get_options_flow since no options_flow.py exists
