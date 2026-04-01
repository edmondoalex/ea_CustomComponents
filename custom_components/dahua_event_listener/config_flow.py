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
                vol.Required("channels", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=256))
            }),
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DahuaOptionsFlowHandler()


class DahuaOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestione delle opzioni (non implementata, placeholder)."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            new_data = {
                **self.config_entry.data,
                "host": user_input["host"],
                "username": user_input["username"],
                "password": user_input["password"],
                "channels": user_input["channels"],
            }
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)

            options = {
                "connect_timeout": user_input["connect_timeout"],
                "read_timeout": user_input["read_timeout"],
                "idle_reconnect_seconds": user_input["idle_reconnect_seconds"],
                "reconnect_delay": user_input["reconnect_delay"],
            }
            return self.async_create_entry(title="", data=options)

        options = self.config_entry.options
        data = self.config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("host", default=data.get("host", "")): str,
                vol.Required("username", default=data.get("username", "")): str,
                vol.Required("password", default=data.get("password", "")): str,
                vol.Required("channels", default=data.get("channels", 1)): vol.All(vol.Coerce(int), vol.Range(min=1, max=256)),
                vol.Optional("connect_timeout", default=options.get("connect_timeout", 10)): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
                vol.Optional("read_timeout", default=options.get("read_timeout", 60)): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional("idle_reconnect_seconds", default=options.get("idle_reconnect_seconds", 120)): vol.All(vol.Coerce(int), vol.Range(min=30, max=600)),
                vol.Optional("reconnect_delay", default=options.get("reconnect_delay", 5)): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }),
        )
