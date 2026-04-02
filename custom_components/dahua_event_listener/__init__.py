import logging
import json
import time
import threading
import requests
from requests.auth import HTTPDigestAuth

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import DahuaDataCoordinator

_LOGGER = logging.getLogger(__name__)


def start_dahua_stream(
    hass: HomeAssistant,
    coordinator: DahuaDataCoordinator,
    url: str,
    username: str,
    password: str,
    stop_event: threading.Event,
    reconnect_delay: int,
    read_timeout: int,
    connect_timeout: int,
    idle_reconnect_seconds: int,
):
    """Avvia il listener eventi Dahua con reconnect e stop pulito."""
    reconnect_delay = max(1, int(reconnect_delay))
    read_timeout = max(5, int(read_timeout))
    connect_timeout = max(5, int(connect_timeout))
    idle_reconnect_seconds = max(30, int(idle_reconnect_seconds))

    while not stop_event.is_set():
        try:
            _LOGGER.info("Connessione stream Dahua: %s", url)
            with requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                stream=True,
                timeout=(connect_timeout, read_timeout),
            ) as response:
                buffer = []
                last_data_ts = time.monotonic()

                for line_bytes in response.iter_lines():
                    if stop_event.is_set():
                        break

                    if not line_bytes:
                        if time.monotonic() - last_data_ts > idle_reconnect_seconds:
                            _LOGGER.warning("Nessun evento da %ss, reconnessione stream", idle_reconnect_seconds)
                            break
                        continue

                    last_data_ts = time.monotonic()
                    line = line_bytes.decode("utf-8", errors="ignore").strip()

                    if line.startswith("--"):
                        if buffer:
                            block = "\n".join(buffer)
                            buffer.clear()

                            if "Heartbeat" in block:
                                continue

                            try:
                                if "data=" not in block:
                                    # Alcuni Dahua inviano eventi senza payload JSON.
                                    # In questo caso estraiamo almeno Code/action/index dagli header.
                                    headers = block
                                    data = {}
                                else:
                                    headers, body = block.split("data=", 1)
                                    data = json.loads(body.strip())

                                _LOGGER.debug("Blocco ricevuto:\n%s", block)
                                _LOGGER.debug("Headers: %s", headers)
                                if data:
                                    _LOGGER.debug("Body JSON:\n%s", json.dumps(data, indent=2))

                                code = ""
                                action = ""
                                index = None

                                header_lines = headers.strip().split("\n")[1:] if "Content-Length" in headers else headers.strip().split("\n")

                                for line in header_lines:
                                    for part in line.replace("\r", "").split(";"):
                                        if part.startswith("Code="):
                                            code = part.split("=", 1)[1]
                                        elif part.startswith("action="):
                                            action = part.split("=", 1)[1]
                                        elif part.startswith("index="):
                                            try:
                                                index = int(part.split("=", 1)[1]) + 1
                                            except ValueError:
                                                index = None

                                code = code or data.get("Event", "")

                                if code == "RtspSessionDisconnect":
                                    continue

                                temperature = None
                                if data:
                                    try:
                                        info = data.get("Info", [{}])[0]
                                        temperature = info.get("Temperature")
                                    except Exception as ex:
                                        _LOGGER.debug("Nessuna temperatura o parsing fallito: %s", ex)

                                coordinator_data = {
                                    "code": code,
                                    "action": action,
                                    "index": index,
                                    "data": data,
                                    "temperature": temperature,
                                }

                                _LOGGER.info(
                                    "Evento ricevuto: codice=%s azione=%s indice=%s temperatura=%s",
                                    code, action, index, temperature
                                )

                                hass.loop.call_soon_threadsafe(
                                    coordinator.async_set_updated_data,
                                    coordinator_data
                                )

                            except Exception as e:
                                _LOGGER.exception("Errore parsing evento Dahua: %s", e)
                    else:
                        buffer.append(line)

        except requests.exceptions.ReadTimeout:
            _LOGGER.warning("Timeout lettura stream Dahua, riconnessione")
        except requests.exceptions.RequestException as e:
            _LOGGER.warning("Errore connessione stream Dahua: %s", e)
        except Exception as e:
            _LOGGER.exception("Errore stream Dahua: %s", e)

        if not stop_event.is_set():
            time.sleep(reconnect_delay)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup dell'integrazione da UI."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    user = entry.data["username"]
    pwd = entry.data["password"]
    name = entry.data["name"]

    url = f"http://{host}/cgi-bin/eventManager.cgi?action=attach&codes=[All]&heartbeat=5"

    _LOGGER.info("Avvio listener eventi Dahua per '%s' su %s", name, host)

    coordinator = DahuaDataCoordinator(hass, entry.entry_id)
    stop_event = threading.Event()
    options = entry.options or {}
    reconnect_delay = int(options.get("reconnect_delay", 5))
    read_timeout = int(options.get("read_timeout", 60))
    connect_timeout = int(options.get("connect_timeout", 10))
    idle_reconnect_seconds = int(options.get("idle_reconnect_seconds", 120))
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "name": name,
        "stop_event": stop_event,
        "reconnect_delay": reconnect_delay,
        "read_timeout": read_timeout,
        "connect_timeout": connect_timeout,
        "idle_reconnect_seconds": idle_reconnect_seconds,
    }

    hass.async_add_executor_job(
        start_dahua_stream,
        hass,
        coordinator,
        url,
        user,
        pwd,
        stop_event,
        reconnect_delay,
        read_timeout,
        connect_timeout,
        idle_reconnect_seconds,
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "camera"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "camera"])
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data and entry_data.get("stop_event"):
            entry_data["stop_event"].set()
    return unload_ok
