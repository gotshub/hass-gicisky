"""Parser for Gicisky BLE advertisements.

This file is shamlessly copied from the following repository:
https://github.com/Ernst79/bleparser/blob/c42ae922e1abed2720c7fac993777e1bd59c0c93/package/bleparser/Gicisky.py

MIT License applies.
"""

from __future__ import annotations

from sensor_state_data import (
    DeviceClass,
    DeviceKey,
    SensorDescription,
    SensorDeviceInfo,
    SensorUpdate,
    SensorValue,
    Units,
)

from .devices import SLEEPY_DEVICE_MODELS
from .parser import GiciskyBluetoothDeviceData

__version__ = "1.0.0"

__all__ = [
    "SLEEPY_DEVICE_MODELS",
    "GiciskyBluetoothDeviceData",
    "SensorDescription",
    "SensorDeviceInfo",
    "DeviceClass",
    "DeviceKey",
    "SensorUpdate",
    "SensorDeviceInfo",
    "SensorValue",
    "Units",
]
