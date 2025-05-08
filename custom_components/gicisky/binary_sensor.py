"""Support for Gicisky binary sensors."""

from __future__ import annotations

from .gicisky_ble.parser import (
    BinarySensorDeviceClass as GiciskyBinarySensorDeviceClass,
    ExtendedBinarySensorDeviceClass,
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
from .types import GiciskyBLEConfigEntry

BINARY_SENSOR_DESCRIPTIONS = {
    GiciskyBinarySensorDeviceClass.BATTERY: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.BATTERY,
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    GiciskyBinarySensorDeviceClass.DOOR: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.DOOR,
        device_class=BinarySensorDeviceClass.DOOR,
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
    GiciskyBinarySensorDeviceClass.OCCUPANCY: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.OCCUPANCY,
        device_class=BinarySensorDeviceClass.OCCUPANCY,
    ),
    GiciskyBinarySensorDeviceClass.OPENING: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.OPENING,
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    GiciskyBinarySensorDeviceClass.POWER: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.POWER,
        device_class=BinarySensorDeviceClass.POWER,
    ),
    GiciskyBinarySensorDeviceClass.SMOKE: BinarySensorEntityDescription(
        key=GiciskyBinarySensorDeviceClass.SMOKE,
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
    ExtendedBinarySensorDeviceClass.ANTILOCK: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.ANTILOCK,
    ),
    ExtendedBinarySensorDeviceClass.ARMED: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.ARMED,
        icon="mdi:shield-check",
    ),
    ExtendedBinarySensorDeviceClass.CHILDLOCK: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.CHILDLOCK,
    ),
    ExtendedBinarySensorDeviceClass.DEVICE_FORCIBLY_REMOVED: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.DEVICE_FORCIBLY_REMOVED,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    ExtendedBinarySensorDeviceClass.DOOR_LEFT_OPEN: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.DOOR_LEFT_OPEN,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    ExtendedBinarySensorDeviceClass.DOOR_STUCK: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.DOOR_STUCK,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    ExtendedBinarySensorDeviceClass.FINGERPRINT: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.FINGERPRINT,
        icon="mdi:fingerprint",
    ),
    ExtendedBinarySensorDeviceClass.KNOCK_ON_THE_DOOR: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.KNOCK_ON_THE_DOOR,
    ),
    ExtendedBinarySensorDeviceClass.PRY_THE_DOOR: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.PRY_THE_DOOR,
        device_class=BinarySensorDeviceClass.TAMPER,
    ),
    ExtendedBinarySensorDeviceClass.TOOTHBRUSH: BinarySensorEntityDescription(
        key=ExtendedBinarySensorDeviceClass.TOOTHBRUSH,
    ),
}


def sensor_update_to_bluetooth_data_update(
    sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate[bool | None]:
    """Convert a sensor update to a bluetooth data update."""
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
    entry: GiciskyBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gicisky BLE sensors."""
    coordinator = entry.runtime_data
    processor = GiciskyPassiveBluetoothDataProcessor(
        sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            GiciskyBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, BinarySensorEntityDescription)
    )


class GiciskyBluetoothSensorEntity(
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
