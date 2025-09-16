import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class AlisteOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    "username",
                    default=self.config_entry.options.get(
                        "username", self.config_entry.data["username"]
                    ),
                ): str,
                vol.Required(
                    "password",
                    default=self.config_entry.options.get(
                        "password", self.config_entry.data["password"]
                    ),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
