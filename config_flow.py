import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class DahuaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestione del flusso di configurazione per Dahua Event Listener."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Primo step di configurazione."""
        if user_input is not None:
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{user_input['name']}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("host"): str,
                vol.Required("username"): str,
                vol.Required("password"): str,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DahuaOptionsFlowHandler(config_entry)


class DahuaOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestione delle opzioni (non implementata, placeholder)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
