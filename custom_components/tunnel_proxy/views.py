from homeassistant.components.http import HomeAssistantView
import logging
import json
import os
import subprocess

_LOGGER = logging.getLogger(__name__)

class TunnelCreateView(HomeAssistantView):
    url = "/api/tunnel_proxy/create"
    name = "api:tunnel_proxy:create"
    requires_auth = False

    def __init__(self, hass):
        self.hass = hass

    async def post(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return self.json({"error": "Missing token"}, status_code=401)
        token = auth[7:]
        token_path = self.hass.config.path("server_tokens.json")
        if not os.path.exists(token_path):
            return self.json({"error": "Token file missing"}, status_code=401)
        with open(token_path, "r") as f:
            tokens = json.load(f)
        if not any(entry["token"] == token for entry in tokens):
            return self.json({"error": "Invalid token"}, status_code=401)

        body = await request.json()
        local_port = body.get("local_port")
        target_ip = body.get("target_ip")
        target_port = body.get("target_port")

        if not local_port or not target_ip or not target_port:
            return self.json({"error": "Missing parameters"}, status_code=400)

        # Crea tunnel con socat
        try:
            subprocess.Popen([
                "socat",
                f"TCP-LISTEN:{local_port},fork",
                f"TCP:{target_ip}:{target_port}"
            ])
        except Exception as e:
            _LOGGER.error(f"Errore avviando socat: {e}")
            return self.json({"error": f"Failed to create tunnel: {e}"}, status_code=500)

        # Salva su file
        tunnels_path = self.hass.config.path("tunnels.json")
        tunnels = []
        if os.path.exists(tunnels_path):
            with open(tunnels_path, "r") as f:
                try:
                    tunnels = json.load(f)
                except Exception:
                    tunnels = []

        tunnels.append({
            "local_port": local_port,
            "target_ip": target_ip,
            "target_port": target_port
        })

        with open(tunnels_path, "w") as f:
            json.dump(tunnels, f, indent=2)

        _LOGGER.info(f"✅ Tunnel creato: {local_port} -> {target_ip}:{target_port}")
        return self.json({"status": "Tunnel created"})
