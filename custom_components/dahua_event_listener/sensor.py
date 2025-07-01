from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DahuaDataCoordinator, DahuaEntity

SENSORS = [
    ("code", "Codice Evento"),
    ("action", "Azione Evento"),
    ("temperature", "Temperatura"),
    ("latitude", "Latitudine"),
    ("longitude", "Longitudine"),
    ("raw", "Dati Grezzi"),
]


def extract_value(data: dict, key: str):
    try:
        if key == "temperature":
            return data.get("data", {}).get("Info", [{}])[0].get("Temperature")
        elif key == "latitude":
            lat = data.get("data", {}).get("Info", [{}])[0].get("GPS", {}).get("Latitude")
            return round(lat / 1e6, 6) if lat else None
        elif key == "longitude":
            lon = data.get("data", {}).get("Info", [{}])[0].get("GPS", {}).get("Longitude")
            return round(lon / 1e6, 6) if lon else None
        elif key == "raw":
            return str(data.get("data", {}))[:255]  # Evita errori di lunghezza
        else:
            return data.get(key)
    except Exception:
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: DahuaDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    name_prefix = entry.data.get("name", entry.entry_id)

    entities = [
        DahuaSensor(coordinator, entry.entry_id, key, f"{name_prefix} {name}")
        for key, name in SENSORS
    ]
    async_add_entities(entities)


class DahuaSensor(DahuaEntity, SensorEntity):
    def __init__(self, coordinator: DahuaDataCoordinator, entry_id: str, key: str, name: str):
        unique_id = f"{entry_id}_{key}"
        super().__init__(coordinator, entry_id, f"{name}", unique_id)
        self._key = key

    @property
    def native_value(self):
        return extract_value(self.coordinator.data, self._key)
