import json
import subprocess
import os

def start_tcp_tunnel(remote_port, target_ip, target_port):
    subprocess.Popen([
        "socat",
        f"TCP-LISTEN:{remote_port},fork,reuseaddr",
        f"TCP:{target_ip}:{target_port}"
    ])

def save_tunnel_info(hass, tunnel_data):
    path = hass.config.path("active_tunnels.json")
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                tunnels = json.load(f)
        else:
            tunnels = []
    except:
        tunnels = []

    if tunnel_data not in tunnels:
        tunnels.append(tunnel_data)
        with open(path, "w") as f:
            json.dump(tunnels, f, indent=2)
