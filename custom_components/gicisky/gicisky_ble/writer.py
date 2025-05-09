from __future__ import annotations

import dataclasses
import logging
import asyncio
import abc
import enum
import math
import struct
import time
import os

from PIL import Image, ImageOps
from bleak import BleakClient, BleakError
from typing import Any, Callable, Tuple, TypeVar, cast
from asyncio import Event, wait_for, sleep
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from .devices import DeviceEntry

_LOGGER = logging.getLogger(__name__)

WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

class BleakCharacteristicMissing(BleakError):
    """Raised when a characteristic is missing from a service."""

class BleakServiceMissing(BleakError):
    """Raised when a service is missing."""


async def write_image(ble_device: BLEDevice, device: DeviceEntry, binary):
    try:
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        if client.is_connected:
            char_uuids = []
            advertised_uuids = ble_device.metadata.get("uuids", [])
            services = await client.get_services()
            for service in services:
                if service.uuid in advertised_uuids:
                    for char in service.characteristics:
                        char_uuids.append(char.uuid)
            _LOGGER.info("  Characteristic UUID: %s", char_uuids)
            if len(char_uuids) == 3:
                gicisky = GiciskyClient(client, char_uuids, device)
                await gicisky.start_notify()
                await gicisky.write_image(binary)
                await gicisky.stop_notify()
            await client.disconnect()
    except:
        await client.disconnect()

    
class BLETransport():
    _event: Event | None
    _command_data: bytearray | None
    def __init__(self, client: BleakClient):
        self._client = client
        self._command_data = None
        self._event = Event()

    def disconnect_on_missing_services(func: WrapFuncType) -> WrapFuncType:
        """Decorator to handle disconnection on missing services/characteristics."""
        async def wrapper(self, *args: Any, **kwargs: Any):
            try:
                return await func(self, *args, **kwargs)
            except (BleakServiceMissing, BleakCharacteristicMissing) as ex:
                if self._client.is_connected:
                    await self._client.clear_cache()
                    await self._client.disconnect()
                raise
        return cast(WrapFuncType, wrapper)
    
    async def read(self) -> bytes:
        return await self.read_notify(30)

    async def write(self, uuid: str, data: bytes):
        return await self.write_ble(uuid, data)
    
    async def read_notify(self, timeout: int) -> bytes:
        """Wait for notification data to be received within the timeout."""
        await wait_for(self._event.wait(), timeout=timeout)
        data = self._command_data
        self._command_data = None
        self._event.clear()  # Reset the event for the next notification
        return data

    #@disconnect_on_missing_services
    async def write_ble(self, uuid: str, data: bytes):
        """Write data to the BLE characteristic."""
        _LOGGER.info("Write UUID: %s, %s", uuid, data)
        await self._client.write_gatt_char(uuid, data)

    def _notification_handler(self, _: Any, data: bytearray):
        """Handle incoming notifications and store the received data."""
        self._command_data = data
        _LOGGER.info("Recv : %s", data)
        self._event.set()  # Notify the waiting coroutine that data has arrived
    
    #@disconnect_on_missing_services
    async def start_notify(self, uuid: str):
        """Start notifications from the BLE characteristic."""
        await self._client.start_notify(uuid, self._notification_handler)
        await sleep(0.5)

    async def stop_notify(self, uuid: str):
        """Stop notifications from the BLE characteristic."""
        await self._client.stop_notify(uuid)

class GiciskyClient:
    def __init__(self, client: BleakClient, uuids, device: DeviceEntry):
        self._transport = BLETransport(client)
        self._packetbuf = bytearray()
        self._cmd_uuid = uuids[0]
        self._img_uuid = uuids[1]
        self._device = device
        

    async def start_notify(self):
        await self._transport.start_notify(self._cmd_uuid)

    async def stop_notify(self):
        await self._transport.stop_notify(self._cmd_uuid)

    async def write_image(self, binary):
        self.image_packet = self.get_image_packet(binary)
        await self._transport.write_ble(self._cmd_uuid, self.get_cmd_packet(0x01))
        while True:
            data = await self._transport.read()
            if data[0] == 0x01:
                if len(data) < 3 or data[1] != 0xf4 or data[2] != 0x00:
                    break
                await self._transport.write_ble(self._cmd_uuid, self.get_cmd_packet(0x02))
                
            elif data[0] == 0x02:
                await self._transport.write_ble(self._cmd_uuid, self.get_cmd_packet(0x03))

            elif data[0] == 0x05:
                if len(data) < 6:
                    break
                if data[1] == 0x08:
                    # End 상태 처리
                    break
                elif data[1] == 0x00:
                    part = (data[5] << 24) | (data[4] << 16) | (data[3] << 8) | data[2]
                    await self._transport.write_ble(self._img_uuid, self.get_img_packet(part))
    

    def get_image_packet(self, binary):
        current_byte = 0
        current_byte_red = 0
        bit_position = 7
        byte_data = []
        byte_data_red = []
        image_packet = []
        image_data, image_data_red = binary
        image_pixel = list(image_data.getdata())
        image_pixel_red = list(image_data_red.getdata())
        width, height = self._device.resolution
        red = self._device.red
        #for pixel in image_data:
        for x in range(width):
            for y in range(height):
                
                pos = (y * width) + x
                if red:
                    pixel = image_pixel[pos]
                    if pixel > 100:                    
                        current_byte |= (1 << bit_position)
                    pixel_red = image_pixel_red[pos]
                    if pixel_red > 100:                    
                        current_byte_red |= (1 << bit_position)
                else:
                    pixel = image_pixel[pos]
                    if pixel > 100:                    
                        current_byte |= (1 << bit_position)

                bit_position -= 1

                if bit_position < 0:
                    byte_data.append(current_byte)
                    byte_data_red.append(current_byte_red)
                    current_byte = 0
                    current_byte_red = 0
                    bit_position = 7
            
        if bit_position != 7:
            byte_data.append(current_byte)
            byte_data_red.append(current_byte_red)

        # image_packet_에 데이터를 채움
        for byte in byte_data:
            image_packet.append(byte)
        #print(image_packet)
        #print(f"image Size({len(image_packet)})")

        if red:
            for byte in byte_data_red:
                image_packet.append(byte)

        return image_packet

    def get_cmd_packet(self, cmd):
        width, height = self._device.resolution
        red = self._device.red
        if cmd == 0x02:
            size = (width * height) // 8
            if red:
                size *= 2
            packet = bytearray(8)  # cmd(1) + size(4) + 고정된 바이트(3)
            packet[0] = cmd
            struct.pack_into('<I', packet, 1, size)
            packet[-3:] = b'\x00\x00\x00'
        else:
            packet = bytearray([cmd])
        return packet
    
    def get_img_packet(self, part):
        width, height = self._device.resolution
        red = self._device.red
        total_size = (width * height) // 8
        if red:
            total_size *= 2
        start_idx = part * 240
        len_to_send = min(240, total_size - start_idx)
        packet = bytearray(4 + len_to_send)
        struct.pack_into('<I', packet, 0, part)
        packet[4:] = self.image_packet[start_idx:start_idx + len_to_send]
        return packet