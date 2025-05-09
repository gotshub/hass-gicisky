"""Support for Gicisky binary sensors."""

from __future__ import annotations

from .gicisky_ble import (
    BinarySensorDeviceClass as GiciskyBinarySensorDeviceClass,
    SensorUpdate,
)

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataUpdate,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info

from .coordinator import GiciskyPassiveBluetoothDataProcessor
from .device import device_key_to_bluetooth_entity_key
from .types import GiciskyConfigEntry

BINARY_SENSOR_DESCRIPTIONS = {
    GiciskyBinarySensorDeviceClass.BATTERY: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.BATTERY,
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    GiciskyBinarySensorDeviceClass.BATTERY_CHARGING: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.BATTERY_CHARGING,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    GiciskyBinarySensorDeviceClass.CO: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.CO,
        device_class=BinarySensorDeviceClass.CO,
    ),
    GiciskyBinarySensorDeviceClass.COLD: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.COLD,
        device_class=BinarySensorDeviceClass.COLD,
    ),
    GiciskyBinarySensorDeviceClass.CONNECTIVITY: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.CONNECTIVITY,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    GiciskyBinarySensorDeviceClass.DOOR: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.DOOR,
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    GiciskyBinarySensorDeviceClass.HEAT: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.HEAT,
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    GiciskyBinarySensorDeviceClass.GARAGE_DOOR: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.GARAGE_DOOR,
        device_class=BinarySensorDeviceClass.GARAGE_DOOR,
    ),
    GiciskyBinarySensorDeviceClass.GAS: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.GAS,
        device_class=BinarySensorDeviceClass.GAS,
    ),
    GiciskyBinarySensorDeviceClass.GENERIC: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.GENERIC,
    ),
    GiciskyBinarySensorDeviceClass.LIGHT: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.LIGHT,
        device_class=BinarySensorDeviceClass.LIGHT,
    ),
    GiciskyBinarySensorDeviceClass.LOCK: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.LOCK,
        device_class=BinarySensorDeviceClass.LOCK,
    ),
    GiciskyBinarySensorDeviceClass.MOISTURE: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.MOISTURE,
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    GiciskyBinarySensorDeviceClass.MOTION: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.MOTION,
        device_class=BinarySensorDeviceClass.MOTION,
    ),
    GiciskyBinarySensorDeviceClass.MOVING: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.MOVING,
        device_class=BinarySensorDeviceClass.MOVING,
    ),
    GiciskyBinarySensorDeviceClass.OCCUPANCY: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.OCCUPANCY,
        device_class=BinarySensorDeviceClass.OCCUPANCY,
    ),
    GiciskyBinarySensorDeviceClass.OPENING: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.OPENING,
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    GiciskyBinarySensorDeviceClass.PLUG: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.PLUG,
        device_class=BinarySensorDeviceClass.PLUG,
    ),
    GiciskyBinarySensorDeviceClass.POWER: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.POWER,
        device_class=BinarySensorDeviceClass.POWER,
    ),
    GiciskyBinarySensorDeviceClass.PRESENCE: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.PRESENCE,
        device_class=BinarySensorDeviceClass.PRESENCE,
    ),
    GiciskyBinarySensorDeviceClass.PROBLEM: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.PROBLEM,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    GiciskyBinarySensorDeviceClass.RUNNING: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.RUNNING,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    GiciskyBinarySensorDeviceClass.SAFETY: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.SAFETY,
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    GiciskyBinarySensorDeviceClass.SMOKE: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.SMOKE,
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
    GiciskyBinarySensorDeviceClass.SOUND: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.SOUND,
        device_class=BinarySensorDeviceClass.SOUND,
    ),
    GiciskyBinarySensorDeviceClass.TAMPER: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.TAMPER,
        device_class=BinarySensorDeviceClass.TAMPER,
    ),
    GiciskyBinarySensorDeviceClass.VIBRATION: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.VIBRATION,
        device_class=BinarySensorDeviceClass.VIBRATION,
    ),
    GiciskyBinarySensorDeviceClass.WINDOW: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.WINDOW,
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
}


def sensor_update_to_bluetooth_data_update(
    sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate[bool | None]:
    """Convert a binary sensor update to a bluetooth data update."""
    return PassiveBluetoothDataUpdate(
        devices={
            device_id: sensor_device_info_to_hass_device_info(device_info)
            for device_id, device_info in sensor_update.devices.items()
        },
        entity_descriptions={
            device_key_to_bluetooth_entity_key(device_key): BINARY_SENSOR_DESCRIPTIONS[
                description.device_class
            ]
            for device_key, description in sensor_update.binary_entity_descriptions.items()
            if description.device_class
        },
        entity_data={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
            for device_key, sensor_values in sensor_update.binary_entity_values.items()
        },
        entity_names={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.binary_entity_values.items()
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GiciskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gicisky BLE binary sensors."""
    coordinator = entry.runtime_data
    processor = GiciskyPassiveBluetoothDataProcessor(
        sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            GiciskyBluetoothBinarySensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, BinarySensorEntityDescription)
    )


class GiciskyBluetoothBinarySensorEntity(
    PassiveBluetoothProcessorEntity[GiciskyPassiveBluetoothDataProcessor[bool | None]],
    BinarySensorEntity,
):
    """Representation of a Gicisky binary sensor."""

    @property
    def is_on(self) -> bool | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.processor.coordinator.sleepy_device or super().available
