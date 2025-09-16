import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

_SCHEMA = vol.Schema({vol.Required("username"): str, vol.Required("password"): str})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input:
            return self.async_create_entry(title=user_input["username"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_SCHEMA)

    @staticmethod
    def async_get_options_flow(config_entry):
        from .options_flow import OptionsFlow
        return OptionsFlow(config_entry)
