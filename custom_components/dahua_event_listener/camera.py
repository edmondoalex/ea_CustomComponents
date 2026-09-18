from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import DahuaDataCoordinator, DahuaEntity
from .snapshot import fetch_dahua_snapshot


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
        return await self.hass.async_add_executor_job(
            fetch_dahua_snapshot,
            self._host,
            self._username,
            self._password,
            channel,
        )

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
        channel: int
    ):
        Camera.__init__(self)
        DahuaEntity.__init__(self, coordinator, entry_id, name, unique_id)
        self._username = username
        self._password = password
        self._host = host
        self._channel = channel

    async def async_camera_image(self, *args, **kwargs):
        return await self.hass.async_add_executor_job(
            fetch_dahua_snapshot,
            self._host,
            self._username,
            self._password,
            self._channel,
        )

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
                channel=ch
            )
        )

    async_add_entities(entities)
