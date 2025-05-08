"""Support for gicisky ble."""

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .coordinator import GiciskyActiveBluetoothProcessorCoordinator

type GiciskyBLEConfigEntry = ConfigEntry[GiciskyActiveBluetoothProcessorCoordinator]
