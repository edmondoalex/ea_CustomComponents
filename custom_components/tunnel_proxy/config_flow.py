import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)


class TunnelProxyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("id"): str,
                vol.Optional("url", default="http://devices.edmondoalex.it:8000"): str,
            })
        )


class TunnelProxyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_menu()

    async def async_step_menu(self, user_input=None):
        return self.async_show_menu(
            step_id="menu",
            menu_options=["resend_token"]
        )

    async def async_step_resend_token(self, user_input=None):
        name = self.config_entry.data["name"]
        url = self.config_entry.data["url"]

        from .token_manager import get_existing_token, send_token
        token_path = self.config_entry.hass.config.path("server_tokens.json")
        token = await self.config_entry.hass.async_add_executor_job(
            get_existing_token, token_path, name, url
        )

        if token:
            await self.config_entry.hass.async_add_executor_job(send_token, url, name, token)
            return self.async_create_entry(title="Token reinviato", data={})
        else:
            return self.async_abort(reason="no_token_found")


def get_options_flow(config_entry):
    return TunnelProxyOptionsFlow(config_entry)
