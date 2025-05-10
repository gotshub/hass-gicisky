# gicisky_ble.py

from __future__ import annotations
from enum import Enum
import logging
import struct
from typing import Any, Callable, TypeVar
from asyncio import Event, wait_for, sleep
from PIL import Image
from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .devices import DeviceEntry
from .const import SERVICE_GICISKY

_LOGGER = logging.getLogger(__name__)

# 예외 정의
class BleakCharacteristicMissing(BleakError):
    """Characteristic Missing"""

class BleakServiceMissing(BleakError):
    """Service Missing"""

WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

def disconnect_on_missing_services(func: WrapFuncType) -> WrapFuncType:
    """Missing services"""
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except (BleakServiceMissing, BleakCharacteristicMissing):
            if self.client.is_connected:
                await self.client.clear_cache()
                await self.client.disconnect()
            raise
    return wrapper  # type: ignore

async def update_image(
    ble_device: BLEDevice,
    device: DeviceEntry,
    image: Image
) -> bool:
    client: BleakClient | None = None
    try:
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        services = client.services
        # SERVICE_GICISKY 특성 UUID 수집
        char_uuids = [
            c.uuid
            for svc in services if svc.uuid == SERVICE_GICISKY
            for c in svc.characteristics
        ]
        if len(char_uuids) != 3:
            raise BleakServiceMissing(f"UUID Len: {len(char_uuids)}")
        gicisky = GiciskyClient(client, char_uuids, device)
        await gicisky.start_notify()
        await gicisky.write_image(image)
        await gicisky.stop_notify()
        return True
    except Exception as e:
        _LOGGER.error("Fail image write: %s", e)
        return False
    finally:
        if client and client.is_connected:
            await client.disconnect()

class GiciskyClient:
    class Status(Enum):
        START = 0
        SIZE_DATA = 1
        IMAGE = 2
        IMAGE_DATA = 3
        
    def __init__(
        self,
        client: BleakClient,
        uuids: list[str],
        device: DeviceEntry
    ) -> None:
        self.client = client
        self.cmd_uuid, self.img_uuid = uuids[:2]
        self.width = device.width
        self.height = device.height
        self.support_red = device.red
        self.packet_size = (self.width * self.height) // 8 * (2 if self.support_red else 1)
        self.event: Event = Event()
        self.command_data: bytes | None = None
        self.image_packets: list[int] = []

    @disconnect_on_missing_services
    async def start_notify(self) -> None:
        await self.client.start_notify(self.cmd_uuid, self._notification_handler)
        await sleep(0.5)

    @disconnect_on_missing_services
    async def stop_notify(self) -> None:
        await self.client.stop_notify(self.cmd_uuid)

    @disconnect_on_missing_services
    async def write(self, uuid: str, data: bytes) -> None:
        _LOGGER.debug("Write UUID=%s data=%s", uuid, data.hex())
        for i in range(0, len(data), 20):
            await self.client.write_gatt_char(uuid, data[i : i + 20])
            await sleep(0.05)

    def _notification_handler(self, _: Any, data: bytearray) -> None:
        self.command_data = bytes(data)
        self.event.set()

    async def read(self, timeout: float = 30.0) -> bytes:
        await wait_for(self.event.wait(), timeout)
        data = self.command_data or b""
        self.command_data = None
        self.event.clear()
        _LOGGER.debug("Received: %s", data.hex())
        return data

    async def write_with_response(self, uuid, packet: bytes) -> bytes:
        await self.write(uuid, packet)
        return await self.read()
    
    async def write_start_with_response(self) -> bytes:
        return await self.write_with_response(self.cmd_uuid, self._make_cmd_packet(0x01))

    async def write_size_with_response(self) -> bytes:
        return await self.write_with_response(self.cmd_uuid, self._make_cmd_packet(0x02))

    async def write_start_image_with_response(self) -> bytes:
        return await self.write_with_response(self.cmd_uuid, self._make_cmd_packet(0x03))

    async def write_image_with_response(self, part:int) -> bytes:
        return await self.write_with_response(self.img_uuid, self._make_img_packet(part))
    
    async def write_image(self, image: Image) -> None:
        _LOGGER.info("Write Image")
        part = 0
        status = self.Status.START
        self.image_packets = self._make_image_packets(image)
        try:
            while True:
                if status == self.Status.START:
                    data = await self.write_start_with_response()
                    if len(data) < 3 or data[0] != 0x01 or data[1] != 0xF4 or data[2] != 0x00:
                        raise Exception(f"Packet Error: {data}")
                    status = self.Status.SIZE_DATA
                
                elif status == self.Status.SIZE_DATA:  
                    data = await self.write_size_with_response()
                    if len(data) < 1 or data[0] != 0x02:
                        raise Exception(f"Packet Error: {data}")
                    status = self.Status.IMAGE

                elif status == self.Status.IMAGE:  
                    data = await self.write_start_image_with_response()
                    if len(data) < 6 or data[0] != 0x05 or data[1] != 0x00:
                        raise Exception(f"Packet Error: {data}")
                    status = self.Status.IMAGE_DATA

                elif status == self.Status.IMAGE_DATA:  
                    data = await self.write_image_with_response(part)
                    if len(data) < 6 or data[0] != 0x05 or data[1] != 0x00:
                        break
                    part = int.from_bytes(data[2:6], "little")
                else:
                    break
        except Exception as e:
            _LOGGER.error("Write Error: %s", e)
        finally:
            _LOGGER.info("Finish")

    def _make_image_packets(self, image: Image) -> list[int]:
        threshold = 195
        red_channel = image.split()[0]  # R (Red) 채널 추출
        binary = image.convert('L')  # 그레이스케일로 변환
        binary = binary.point(lambda x: 255 if x > threshold else 0, mode='1')
        binary_red = red_channel.point(lambda x: 255 if x > threshold else 0, mode='1')
        packets = bytearray()
        channels = (binary, binary_red) if self.support_red else (binary,)
        for img in channels:
            pixels = img.getdata()
            byte = 0
            bit = 7
            for pix in pixels:
                if pix > 0:
                    byte |= 1 << bit
                bit -= 1
                if bit < 0:
                    packets.append(byte)
                    byte = 0
                    bit = 7
            if bit != 7:
                packets.append(byte)
        return list(packets)

    def _make_cmd_packet(self, cmd: int) -> bytes:
        if cmd == 0x02:
            packet = bytearray(8)
            packet[0] = cmd
            struct.pack_into("<I", packet, 1, self.packet_size)
            packet[-3:] = b"\x00\x00\x00"
            return bytes(packet)
        return bytes([cmd])

    def _make_img_packet(self, part: int) -> bytes:
        start = part * 240
        chunk = self.image_packets[start : start + min(240, self.packet_size - start)]
        packet = bytearray(4 + len(chunk))
        struct.pack_into("<I", packet, 0, part)
        packet[4:] = bytes(chunk)
        return bytes(packet)
