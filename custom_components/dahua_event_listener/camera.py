from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from urllib.parse import quote

from .const import DOMAIN
from .coordinator import DahuaDataCoordinator, DahuaEntity

import requests
from requests.auth import HTTPDigestAuth


class DahuaSnapshotCamera(DahuaEntity, Camera):
    """Snapshot dinamico dal canale dell'ultimo evento."""
    def __init__(
        self,
        coordinator: DahuaDataCoordinator,
        entry_id: str,
        name: str,
        unique_id: str,
        username: str,
        password: str,
        host: str
    ):
        Camera.__init__(self)
        DahuaEntity.__init__(self, coordinator, entry_id, name, unique_id)
        self._username = username
        self._password = password
        self._host = host

    async def async_camera_image(self, *args, **kwargs):
        channel = self.coordinator.data.get("index") if self.coordinator.data else 1
        snapshot_url = f"http://{self._host}/cgi-bin/snapshot.cgi?channel={channel}&stream=0"

        def fetch_snapshot():
            try:
                response = requests.get(
                    snapshot_url,
                    auth=HTTPDigestAuth(self._username, self._password),
                    timeout=10
                )
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                self._logger.error("Errore snapshot (evento index): %s", e)
            return None

        return await self.hass.async_add_executor_job(fetch_snapshot)

    @property
    def name(self):
        return self._attr_name

    @property
    def is_streaming(self):
        return False

    @property
    def supported_features(self):
        return CameraEntityFeature(0)

    async def async_get_supported_features(self) -> int:
        return self.supported_features

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "Ultimo canale attivo": data.get("index") if data else "N/D"
        }


class DahuaRuleSnapshotCamera(DahuaSnapshotCamera):
    """Foto memorizzata esclusivamente all'avvio di una regola valida."""

    async def async_camera_image(self, *args, **kwargs):
        return self.coordinator.last_rule_snapshot

    @property
    def extra_state_attributes(self):
        snapshot_info = self.coordinator.last_rule_snapshot_info
        return {
            "Ultima regola fotografata": snapshot_info.get("rule_name", "N/D"),
            "Canale ultima foto": snapshot_info.get("channel", "N/D"),
            "Codice evento": snapshot_info.get("code", "N/D"),
            "Azione evento": snapshot_info.get("action", "N/D"),
            "Data ultima foto": snapshot_info.get("captured_at"),
        }


class DahuaStaticChannelCamera(DahuaEntity, Camera):
    """Snapshot statico da un canale specifico (CH1, CH2, ecc.)."""
    def __init__(
        self,
        coordinator: DahuaDataCoordinator,
        entry_id: str,
        name: str,
        unique_id: str,
        username: str,
        password: str,
        host: str,
        channel: int,
        rtsp_port: int,
        rtsp_subtype: int,
        use_rtsp_for_stills: bool,
    ):
        Camera.__init__(self)
        DahuaEntity.__init__(self, coordinator, entry_id, name, unique_id)
        self._username = username
        self._password = password
        self._host = host
        self._channel = channel
        self._rtsp_port = rtsp_port
        self._rtsp_subtype = rtsp_subtype
        self._use_rtsp_for_stills = use_rtsp_for_stills

    async def async_camera_image(self, *args, **kwargs):
        snapshot_url = f"http://{self._host}/cgi-bin/snapshot.cgi?channel={self._channel}&stream=0"

        def fetch_snapshot():
            try:
                response = requests.get(
                    snapshot_url,
                    auth=HTTPDigestAuth(self._username, self._password),
                    timeout=10
                )
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                self._logger.error("Errore snapshot canale %s: %s", self._channel, e)
            return None

        return await self.hass.async_add_executor_job(fetch_snapshot)

    @property
    def name(self):
        return self._attr_name

    @property
    def is_streaming(self):
        return False

    @property
    def supported_features(self):
        return CameraEntityFeature.STREAM

    @property
    def use_stream_for_stills(self) -> bool:
        """Usa RTSP per le immagini solo sui canali configurati."""
        return self._use_rtsp_for_stills

    async def async_get_supported_features(self) -> int:
        return self.supported_features

    async def stream_source(self) -> str:
        """Restituisce il flusso RTSP del canale."""
        username = quote(self._username, safe="")
        password = quote(self._password, safe="")
        return (
            f"rtsp://{username}:{password}@{self._host}:{self._rtsp_port}"
            f"/cam/realmonitor?channel={self._channel}"
            f"&subtype={self._rtsp_subtype}"
        )

    @property
    def extra_state_attributes(self):
        return {
            "Canale fisso": self._channel,
            "RTSP per snapshot": self._use_rtsp_for_stills,
            "RTSP subtype": self._rtsp_subtype,
        }


def parse_channel_list(value: str, max_channel: int) -> set[int]:
    """Converte una lista tipo '7,14' in un insieme di canali validi."""
    channels = set()
    for item in str(value or "").split(","):
        item = item.strip()
        if not item:
            continue
        try:
            channel = int(item)
        except ValueError:
            continue
        if 1 <= channel <= max_channel:
            channels.add(channel)
    return channels


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    data = entry.data
    coordinator: DahuaDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    name = data["name"]
    host = data["host"]
    user = data["username"]
    pwd = data["password"]
    num_channels = data.get("channels", 1)  # valore aggiunto in config_flow.py
    options = entry.options or {}
    rtsp_port = int(options.get("rtsp_port", data.get("rtsp_port", 554)))
    rtsp_subtype = int(options.get("rtsp_subtype", data.get("rtsp_subtype", 0)))
    rtsp_snapshot_channels = parse_channel_list(
        options.get(
            "rtsp_snapshot_channels",
            data.get("rtsp_snapshot_channels", ""),
        ),
        num_channels,
    )

    entities = []

    # Entita dinamica basata su ultimo evento
    entities.append(
        DahuaSnapshotCamera(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            name=f"{name} (Ultimo Evento)",
            unique_id=f"{entry.entry_id}_camera_event",
            username=user,
            password=pwd,
            host=host
        )
    )

    # Entita' separata aggiornata soltanto da regole valide con action=Start.
    entities.append(
        DahuaRuleSnapshotCamera(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            name=f"{name} (Ultima Regola)",
            unique_id=f"{entry.entry_id}_camera_rule",
            username=user,
            password=pwd,
            host=host
        )
    )

    # Entita statiche per ogni canale
    for ch in range(1, num_channels + 1):
        entities.append(
            DahuaStaticChannelCamera(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                name=f"{name} CH{ch}",
                unique_id=f"{entry.entry_id}_camera_ch{ch}",
                username=user,
                password=pwd,
                host=host,
                channel=ch,
                rtsp_port=rtsp_port,
                rtsp_subtype=rtsp_subtype,
                use_rtsp_for_stills=ch in rtsp_snapshot_channels,
            )
        )

    async_add_entities(entities)
