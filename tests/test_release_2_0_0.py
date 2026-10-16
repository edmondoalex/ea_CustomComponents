import asyncio
import hashlib
import importlib
import json
from pathlib import Path
import sys
import types
import threading

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "dahua_event_listener"


def _install_home_assistant_stubs():
    homeassistant = types.ModuleType("homeassistant")
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object
    core.callback = lambda function: function
    typing = types.ModuleType("homeassistant.helpers.typing")
    typing.ConfigType = dict
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = object
    coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        @classmethod
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, **kwargs):
            self.hass = hass
            self.data = None

        def async_set_updated_data(self, data):
            self.data = data

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

    coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    coordinator.CoordinatorEntity = CoordinatorEntity
    dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
    dispatcher.async_dispatcher_connect = lambda *args, **kwargs: lambda: None
    helpers = types.ModuleType("homeassistant.helpers")
    helpers.typing = typing
    helpers.update_coordinator = coordinator
    helpers.dispatcher = dispatcher
    homeassistant.core = core
    homeassistant.config_entries = config_entries
    homeassistant.helpers = helpers
    sys.modules.update({
        "homeassistant": homeassistant,
        "homeassistant.core": core,
        "homeassistant.config_entries": config_entries,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.typing": typing,
        "homeassistant.helpers.update_coordinator": coordinator,
        "homeassistant.helpers.dispatcher": dispatcher,
    })


class Entry:
    def __init__(self, entry_id, **overrides):
        self.entry_id = entry_id
        self.data = {
            "name": entry_id,
            "host": "192.0.2.10",
            "username": "user",
            "password": "secret",
            "channels": 2,
            "rtsp_port": 554,
            "rtsp_subtype": "0",
        }
        self.options = overrides


class ConfigEntries:
    def __init__(self):
        self.forwarded = []
        self.unloaded = []

    async def async_forward_entry_setups(self, entry, platforms):
        self.forwarded.append((entry.entry_id, tuple(platforms)))

    async def async_unload_platforms(self, entry, platforms):
        self.unloaded.append((entry.entry_id, tuple(platforms)))
        return True


class Hass:
    def __init__(self):
        self.data = {}
        self.config_entries = ConfigEntries()
        self.executor_calls = []

    def async_add_executor_job(self, function, *args):
        self.executor_calls.append((function, args))
        future = asyncio.get_running_loop().create_future()
        future.set_result(None)
        return future


def _load_component():
    _install_home_assistant_stubs()
    sys.path.insert(0, str(ROOT / "custom_components"))
    for name in list(sys.modules):
        if name == "dahua_event_listener" or name.startswith("dahua_event_listener."):
            del sys.modules[name]
    return importlib.import_module("dahua_event_listener")


def test_manifest_license_and_original_assets_are_release_ready():
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {
        "domain": "dahua_event_listener",
        "name": "Dahua Integration",
        "version": "2.0.0",
        "documentation": "https://github.com/edmondoalex/ea_CustomComponents",
        "dependencies": ["stream"],
        "codeowners": ["@lucaed3001"],
        "requirements": [],
        "config_flow": True,
        "integration_type": "hub",
        "iot_class": "local_push",
        "issue_tracker": "https://github.com/edmondoalex/ea_CustomComponents/issues",
    }
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").strip()
    assert not (ROOT / "manifest.json").exists()
    assets = [
        ROOT / "icon.png", ROOT / "logo.png",
        COMPONENT / "icon.png", COMPONENT / "logo.png",
        COMPONENT / "brand" / "icon.png", COMPONENT / "brand" / "logo.png",
    ]
    assert len({hashlib.sha256(path.read_bytes()).hexdigest() for path in assets}) == 1


def test_two_entry_setup_unload_reload_is_isolated_and_idempotent():
    component = _load_component()
    hass = Hass()
    first = Entry("entry-one", host="192.0.2.21", reconnect_delay=9)
    second = Entry("entry-two", host="192.0.2.22", reconnect_delay=11)

    async def scenario():
        assert await component.async_setup_entry(hass, first)
        assert await component.async_setup_entry(hass, second)
        assert set(hass.data[component.DOMAIN]) == {"entry-one", "entry-two"}
        assert hass.executor_calls[0][1][2] == "http://192.0.2.21/cgi-bin/eventManager.cgi?action=attach&codes=[All]&heartbeat=5"
        assert hass.executor_calls[0][1][6] == 9
        assert hass.executor_calls[1][1][2] == "http://192.0.2.22/cgi-bin/eventManager.cgi?action=attach&codes=[All]&heartbeat=5"

        assert await component.async_unload_entry(hass, first)
        assert set(hass.data[component.DOMAIN]) == {"entry-two"}
        assert await component.async_unload_entry(hass, first)
        assert await component.async_unload_entry(hass, second)
        assert component.DOMAIN not in hass.data

        assert await component.async_setup_entry(hass, first)
        assert set(hass.data[component.DOMAIN]) == {"entry-one"}

    asyncio.run(scenario())


def test_public_identity_and_events_remain_stable():
    source = (COMPONENT / "__init__.py").read_text(encoding="utf-8")
    sensor = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    camera = (COMPONENT / "camera.py").read_text(encoding="utf-8")
    assert 'hass.bus.async_fire(f"{DOMAIN}_rule_snapshot", rule_info)' in source
    assert 'f"{entry_id}_{key}"' in sensor
    for suffix in ("camera_event", "camera_rule", "camera_ch{ch}", "camera_rtsp_ch{ch}"):
        assert suffix in camera


def test_stream_parser_keeps_multipart_sequence_and_both_events(monkeypatch):
    component = _load_component()
    stop = threading.Event()
    updates = []

    class Coordinator:
        def set_camera_name(self, channel, name):
            pass

        def async_set_updated_data(self, data):
            updates.append(data)

    class Loop:
        @staticmethod
        def call_soon_threadsafe(function):
            function()

    class StreamHass:
        loop = Loop()

    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def close(self):
            stop.set()

        def iter_lines(self):
            lines = [
                b"--boundary",
                b"Code=VideoMotion;action=Start;index=0",
                b'data={"Event":"VideoMotion"}',
                b"--boundary",
                b"Code=AlarmLocal;action=Stop;index=1",
                b'data={"Event":"AlarmLocal"}',
                b"--boundary",
            ]
            for line in lines:
                yield line
            stop.set()

    response = Response()
    monkeypatch.setattr(component.requests, "get", lambda *args, **kwargs: response)
    slot = {}
    component.start_dahua_stream(
        StreamHass(), Coordinator(),
        "http://192.0.2.10/events", "user", "secret", stop,
        1, 5, 5, 30, slot, threading.Lock(),
    )
    assert [(item["code"], item["action"], item["index"]) for item in updates] == [
        ("VideoMotion", "Start", 1),
        ("AlarmLocal", "Stop", 2),
    ]
    assert slot == {}


def test_unload_keeps_entry_reserved_when_worker_does_not_stop(monkeypatch):
    component = _load_component()

    class StuckHass(Hass):
        def async_add_executor_job(self, function, *args):
            self.executor_calls.append((function, args))
            return asyncio.get_running_loop().create_future()

    async def timeout_immediately(awaitable, timeout):
        if hasattr(awaitable, "close"):
            awaitable.close()
        raise asyncio.TimeoutError

    async def scenario():
        hass = StuckHass()
        entry = Entry("entry-stuck")
        monkeypatch.setattr(component.asyncio, "wait_for", timeout_immediately)
        assert await component.async_setup_entry(hass, entry)
        assert not await component.async_unload_entry(hass, entry)
        assert "entry-stuck" in hass.data[component.DOMAIN]
        assert hass.data[component.DOMAIN]["entry-stuck"]["stop_event"].is_set()

    asyncio.run(scenario())
