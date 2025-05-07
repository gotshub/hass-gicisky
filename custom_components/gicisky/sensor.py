# sensor.py
from homeassistant import config_entries
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorEntity,
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

def _to_data_update(parsed: dict) -> PassiveBluetoothDataUpdate:
    """파싱 결과를 DataUpdate로 변환."""
    update = PassiveBluetoothDataUpdate()

    # 배터리 엔티티 키
    key_batt = PassiveBluetoothEntityKey(key="battery", device_id=None)
    update.entity_descriptions[key_batt] = {
        "key": "battery",
        "name": "Battery",
        "native_unit_of_measurement": PERCENTAGE,
        "device_class": "battery",
    }
    update.entity_data[key_batt] = parsed.get("battery")

    return update

async def async_setup_entry(
    hass, entry: config_entries.ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Sensor 플랫폼 초기화."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    processor = PassiveBluetoothDataProcessor(_to_data_update)

    # 엔티티 리스너 등록
    entry.async_on_unload(
        processor.async_add_entities_listener(
            PassiveBluetoothSensorEntity, async_add_entities
        )
    )
    # coordinator에 프로세서 등록
    entry.async_on_unload(coordinator.async_register_processor(processor))

class PassiveBluetoothSensorEntity(PassiveBluetoothProcessorEntity, SensorEntity):
    """BLE 배터리 센서 엔티티."""

    @property
    def native_value(self):
        return self.processor.entity_data.get(self.entity_key)
