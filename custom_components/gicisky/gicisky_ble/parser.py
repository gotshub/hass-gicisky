from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from bluetooth_sensor_state_data import BluetoothData
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from home_assistant_bluetooth import BluetoothServiceInfoBleak
from sensor_state_data import (
    SensorLibrary,
)

from .devices import DEVICE_TYPES, DeviceEntry

_LOGGER = logging.getLogger(__name__)


class EncryptionScheme(Enum):
    # No encryption is needed to use this device
    NONE = "none"

    # 16 byte encryption key expected
    GICISKY_BINDKEY = "gicisky_bindkey"


def to_mac(addr: bytes) -> str:
    """Return formatted MAC address."""
    return ":".join(f"{i:02X}" for i in addr)

class GiciskyBluetoothDeviceData(BluetoothData):
    """Data for BTHome Bluetooth devices."""

    def __init__(self, bindkey: bytes | None = None) -> None:
        super().__init__()
        self.set_bindkey(bindkey)

        # Data that we know how to parse but don't yet map to the SensorData model.
        self.unhandled: dict[str, Any] = {}

        # Encryption to expect, based on flags in the UUID.
        self.encryption_scheme = EncryptionScheme.NONE

        # The encryption counter can be used to verify that the counter of encrypted
        # advertisements is increasing, to have some replay protection. We always
        # start at zero allow the first message after a restart.
        self.encryption_counter = 0.0

        # The packet_id is used to filter duplicate messages in BTHome V2.
        self.packet_id: float | None = None

        # If True then we have used the provided encryption key to decrypt at least
        # one payload.
        # If False then we have either not seen an encrypted payload, the key is wrong
        # or encryption is not in use
        self.bindkey_verified = False

        # If True then the decryption has failed or has not been verified yet.
        # If False then the decryption has succeeded.
        self.decryption_failed = True

        # If this is True, then we have not seen an advertisement with a payload
        # Until we see a payload, we can't tell if this device is encrypted or not
        self.pending = True

        # The last service_info we saw that had a payload
        # We keep this to help in reauth flows where we want to reprocess and old
        # value with a new bindkey.
        self.last_service_info: BluetoothServiceInfoBleak | None = None

        # If this is True, the device is not sending advertisements in a regular interval
        self.sleepy_device = False

        self.device: DeviceEntry | None = None

    def set_bindkey(self, bindkey: bytes | None) -> None:
        """Set the bindkey."""
        self.bindkey = bindkey
        if bindkey:
            self.cipher: AESCCM | None = AESCCM(bindkey, tag_length=4)
        else:
            self.cipher = None

    def supported(self, data: BluetoothServiceInfoBleak) -> bool:
        if not super().supported(data):
            return False
        return True

    def _start_update(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.info("Parsing Gicisky BLE advertisement data: %s", service_info)
        if 0x5053 in service_info.manufacturer_data:
            #_LOGGER.info("BLE Info: %s", service_info)
            data = service_info.manufacturer_data[0x5053]
            for uuid in service_info.service_uuids:
                #_LOGGER.info("Gicisky %s BLE UUID %s data: %s", service_info.name, uuid, data.hex())
                if self._parse_gicisky(service_info, data):
                    self.last_service_info = service_info
        return None

    def _parse_gicisky(
        self, service_info: BluetoothServiceInfo, data: bytes
    ) -> bool:
        """Parser for Gicisky sensors"""
        if len(data) != 5:
            return False

        # determine the device type
        device_id = data[0]
        bettery_mv = data[1] / 10
        firmware = (data[2] << 8) + data[3]
        try:
            device = DEVICE_TYPES[device_id]
        except KeyError:
            _LOGGER.info("Unknown Gicisky device found. Data: %s", data.hex())
            return False

        self.device = device
        device_type = device.model

        self.device_id = device_id
        self.device_type = device_type

        identifier = service_info.address.replace(":", "")[-8:]
        self.set_title(f"{identifier} ({device.model})")
        self.set_device_name(f"{device.manufacturer} {identifier}")
        self.set_device_type(f"{device.model} {device.resolution}")
        self.set_device_manufacturer(device.manufacturer)
        self.set_device_sw_version(firmware)

        volt = bettery_mv
        min = device.min_voltage
        max = device.max_voltage
        batt = (volt - min) * 100 / (max - min)
        self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, round(batt, 1))
        self.update_predefined_sensor(
            SensorLibrary.VOLTAGE__ELECTRIC_POTENTIAL_VOLT, round(volt, 1)
        )
        return True