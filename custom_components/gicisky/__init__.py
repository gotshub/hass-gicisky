"""The Gicisky Bluetooth integration."""

from __future__ import annotations

from functools import partial
import logging
from .imagegen import *
from .gicisky_ble import GiciskyBluetoothDeviceData, SensorUpdate
from .gicisky_ble.writer import write_image
from homeassistant.components.bluetooth import (
    DOMAIN as BLUETOOTH_DOMAIN,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceRegistry
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util.signal_type import SignalType

from .const import (
    CONF_BINDKEY,
    CONF_DISCOVERED_EVENT_CLASSES,
    DOMAIN,
    GiciskyBleEvent,
)
from .coordinator import GiciskyPassiveBluetoothProcessorCoordinator
from .types import GiciskyConfigEntry

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


def process_service_info(
    hass: HomeAssistant,
    entry: GiciskyConfigEntry,
    device_registry: DeviceRegistry,
    service_info: BluetoothServiceInfoBleak,
) -> SensorUpdate:
    """Process a BluetoothServiceInfoBleak, running side effects and returning sensor data."""
    coordinator = entry.runtime_data
    data = coordinator.device_data
    update = data.update(service_info)

    return update


def format_event_dispatcher_name(
    address: str, event_class: str
) -> SignalType[GiciskyBleEvent]:
    """Format an event dispatcher name."""
    return SignalType(f"{DOMAIN}_event_{address}_{event_class}")


def format_discovered_event_class(address: str) -> SignalType[str, GiciskyBleEvent]:
    """Format a discovered event class."""
    return SignalType(f"{DOMAIN}_discovered_event_class_{address}")


async def async_setup_entry(hass: HomeAssistant, entry: GiciskyConfigEntry) -> bool:
    """Set up Gicisky Bluetooth from a config entry."""
    address = entry.unique_id
    assert address is not None

    data = GiciskyBluetoothDeviceData()

    device_registry = dr.async_get(hass)
    event_classes = set(entry.data.get(CONF_DISCOVERED_EVENT_CLASSES, ()))
    coordinator = GiciskyPassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=partial(process_service_info, hass, entry, device_registry),
        device_data=data,
        discovered_event_classes=event_classes,
        connectable=True,
        entry=entry,
    )
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


    @callback
    # callback for the draw custom service
    async def writeservice(service: ServiceCall) -> None:
        ble_device = async_ble_device_from_address(hass, address)
        binary = await hass.async_add_executor_job(customimage, entry.entry_id, data.device, service, hass)
        entry.runtime_data.device_data.update_connectivity(True)
        await write_image(ble_device, data.device, binary)
        entry.runtime_data.device_data.update_connectivity(False)             

    # register the services
    hass.services.async_register(DOMAIN, "write", writeservice)

    # only start after all platforms have had a chance to subscribe
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GiciskyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
