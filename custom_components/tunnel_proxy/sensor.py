from homeassistant.helpers.entity import Entity
import json
import os
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "tunnel_proxy"

async def async_setup_entry(hass, entry, async_add_entities):
    token_path = hass.config.path("server_tokens.json")
    name = entry.data["name"]
    url = entry.data["url"]

    entity = TunnelTokenSensor(token_path, name, url)
    async_add_entities([entity], update_before_add=True)

class TunnelTokenSensor(Entity):
    def __init__(self, token_path, name, url):
        self._token_path = token_path
        self._name = name
        self._url = url
        self._state = None

    @property
    def unique_id(self):
        return f"tunnel_token_{self._name}_{self._url}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._name}_{self._url}")},
            "name": f"Tunnel Proxy {self._name}",
            "manufacturer": "Custom",
            "model": "Tunnel Token",
        }

    @property
    def name(self):
        return f"Tunnel Token {self._name}"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        try:
            if not os.path.exists(self._token_path):
                _LOGGER.warning(f"File token {self._token_path} non trovato")
                self._state = None
                return
            with open(self._token_path, "r") as f:
                tokens = json.load(f)
            for item in tokens:
                if item["name"] == self._name and item["url"] == self._url:
                    self._state = item["token"]
                    return
            self._state = None
        except Exception as e:
            _LOGGER.error(f"Errore caricando token: {e}")
            self._state = None
