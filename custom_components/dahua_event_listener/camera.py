from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import DahuaDataCoordinator, DahuaEntity
from homeassistant.components.camera import CameraEntityFeature

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

    async def async_camera_image(self):
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
                self._logger.error("❌ Errore snapshot (evento index): %s", e)
            return None

        return await self.hass.async_add_executor_job(fetch_snapshot)

    @property
    def name(self):
        return self._attr_name

    @property
    def is_streaming(self):
        return True

    @property
    def supported_features(self):
        return CameraEntityFeature.STREAM

    async def async_get_supported_features(self) -> int:
        return self.supported_features

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "Ultimo canale attivo": data.get("index") if data else "N/D"
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
        channel: int
    ):
        Camera.__init__(self)
        DahuaEntity.__init__(self, coordinator, entry_id, name, unique_id)
        self._username = username
        self._password = password
        self._host = host
        self._channel = channel

    async def async_camera_image(self):
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
                self._logger.error("❌ Errore snapshot canale %s: %s", self._channel, e)
            return None

        return await self.hass.async_add_executor_job(fetch_snapshot)

    @property
    def name(self):
        return self._attr_name

    @property
    def is_streaming(self):
        return True

    @property
    def supported_features(self):
        return CameraEntityFeature.STREAM

    
    async def async_get_supported_features(self) -> int:
        return self.supported_features

    @property
    def extra_state_attributes(self):
        return {
            "Canale fisso": self._channel
        }


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

    entities = []

    # 📸 Entità dinamica basata su ultimo evento
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

    # 📸 Entità statiche per ogni canale
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
                channel=ch
            )
        )

    async_add_entities(entities)
