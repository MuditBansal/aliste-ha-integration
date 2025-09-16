import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry): self.entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input:
            return self.async_create_entry(title="", data=user_input)
        data = self.entry.options or self.entry.data
        schema = vol.Schema({vol.Required("username", default=data["username"]): str,
                             vol.Required("password", default=data["password"]): str})
        return self.async_show_form(step_id="init", data_schema=schema)
