from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from .token_manager import async_generate_token_and_notify
from .views import TunnelCreateView
from .config_flow import TunnelProxyOptionsFlow
from .sensor import async_setup_entry as sensor_async_setup_entry


import json
import os
import subprocess
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "tunnel_proxy"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    name = entry.data["name"]
    url = entry.data["url"]
    device_id = entry.data["id"]
    await async_generate_token_and_notify(hass, name, url, device_id)

    hass.http.register_view(TunnelCreateView(hass))

    # Ripristina tunnel esistenti
    tunnels_path = hass.config.path("tunnels.json")
    if os.path.exists(tunnels_path):
        try:
            with open(tunnels_path, "r") as f:
                tunnels = json.load(f)
                for tunnel in tunnels:
                    local_port = tunnel["local_port"]
                    target_ip = tunnel["target_ip"]
                    target_port = tunnel["target_port"]
                    subprocess.Popen([
                        "socat",
                        f"TCP-LISTEN:{local_port},fork",
                        f"TCP:{target_ip}:{target_port}"
                    ])
                    _LOGGER.info(f"🔁 Tunnel ripristinato: {local_port} -> {target_ip}:{target_port}")
        except Exception as e:
            _LOGGER.error(f"Errore caricando tunnel: {e}")

    return True
