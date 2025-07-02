from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import DahuaDataCoordinator, DahuaEntity

SENSORS = [
    ("code", "Event Code"),
    ("action", "Event Action"),
    ("index", "Index"),
    ("temperature", "Temperature"),
    ("latitude", "Latitudine"),
    ("longitude", "Longitudine"),
    ("action_data", "Action Data"),
    ("direction", "Direction"),
    ("name", "Rule Name"),
    ("object_action", "Object Action"),
    ("object_type", "Object Type"),
    ("raw", "Raw Data"),
]


def extract_value(data: dict, key: str):
    try:
        event = data.get("data", {})
        info = event.get("Info", [{}])[0] if "Info" in event else {}

        if key == "temperature":
            return info.get("Temperature")
        elif key == "latitude":
            lat = info.get("GPS", {}).get("Latitude")
            return round(lat / 1e6, 6) if lat else None
        elif key == "longitude":
            lon = info.get("GPS", {}).get("Longitude")
            return round(lon / 1e6, 6) if lon else None
        elif key == "action_data":
            return event.get("Action")
        elif key == "direction":
            return event.get("Direction")
        elif key == "name":
            return event.get("Name")
        elif key == "object_action":
            return event.get("Object", {}).get("Action")
        elif key == "object_type":
            return event.get("Object", {}).get("ObjectType")
        elif key == "raw":
            return str(event)[:255]
        elif key == "index":
            return data.get("index")
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
