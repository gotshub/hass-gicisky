"""Parser for Gicisky BLE advertisements.

This file is shamlessly copied from the following repository:
https://github.com/Ernst79/bleparser/blob/c42ae922e1abed2720c7fac993777e1bd59c0c93/package/bleparser/Gicisky.py

MIT License applies.
"""

from __future__ import annotations

from sensor_state_data import (
    BinarySensorDeviceClass,
    DeviceClass,
    DeviceKey,
    SensorDescription,
    SensorDeviceClass,
    SensorDeviceInfo,
    SensorUpdate,
    SensorValue,
    Units,
)

from .devices import SLEEPY_DEVICE_MODELS
from .parser import GiciskyBluetoothDeviceData

__version__ = "1.0.0"

__all__ = [
    "BinarySensorDeviceClass",
    "SLEEPY_DEVICE_MODELS",
    "GiciskyBluetoothDeviceData",
    "SensorDescription",
    "SensorDeviceClass",
    "SensorDeviceInfo",
    "DeviceClass",
    "DeviceKey",
    "SensorUpdate",
    "SensorDeviceInfo",
    "SensorValue",
    "Units",
]
