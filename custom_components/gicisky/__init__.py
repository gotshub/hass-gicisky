import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)

from .const import DOMAIN
from .parser import BLEDataParser

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Config Entry가 설정될 때 호출됩니다."""
    address = entry.data.get("address")  # 사용자가 지정한 BLE 기기 주소
    parser = BLEDataParser()

    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,   # ACTIVE/ PASSIVE 둘 중 하나
        update_method=parser.update,         # 광고 수신 시 호출될 메서드
    )

    # entry_id별로 저장
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # sensor 플랫폼으로 포워딩
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 모든 플랫폼이 준비된 후 스캐닝 시작
    entry.async_on_unload(coordinator.async_start())

    return True
