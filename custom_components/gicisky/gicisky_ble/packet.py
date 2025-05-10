# gicisky_ble.py

from __future__ import annotations
import logging
import struct
from typing import Any, Callable, TypeVar
from asyncio import Event, wait_for, sleep

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .devices import DeviceEntry
from .const import SERVICE_GICISKY

_LOGGER = logging.getLogger(__name__)

# 예외 정의
class BleakCharacteristicMissing(BleakError):
    """Characteristic 누락 시 예외"""

class BleakServiceMissing(BleakError):
    """Service 누락 시 예외"""

WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

def disconnect_on_missing_services(func: WrapFuncType) -> WrapFuncType:
    """서비스/특성 누락 시 안전하게 BLE 연결 해제"""
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except (BleakServiceMissing, BleakCharacteristicMissing):
            if self.client.is_connected:
                await self.client.clear_cache()
                await self.client.disconnect()
            raise
    return wrapper  # type: ignore

async def write_image(
    ble_device: BLEDevice,
    device: DeviceEntry,
    binary: tuple
) -> bool:
    """
    BLEDevice에 연결하여 GiciskyClient로 이미지 전송
    :param ble_device: 스캔된 BLEDevice
    :param device: DeviceEntry(resolution, red 속성 보유)
    :param binary: (흑백 이미지, 레드 이미지) 튜플
    :return: 성공 여부
    """
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
            raise BleakServiceMissing(f"필요한 특성 3개를 찾지 못함: {len(char_uuids)}개 발견")
        gicisky = GiciskyClient(client, char_uuids, device)
        await gicisky.start_notify()
        await gicisky.write_image(binary)
        await gicisky.stop_notify()
        return True
    except Exception as e:
        _LOGGER.error("이미지 전송 실패: %s", e)
        return False
    finally:
        if client and client.is_connected:
            await client.disconnect()

class GiciskyClient:
    """Gicisky EPD 이미지 전송 클라이언트 (BLETransport 통합)"""
    def __init__(
        self,
        client: BleakClient,
        uuids: list[str],
        device: DeviceEntry
    ) -> None:
        self.client = client
        self.cmd_uuid, self.img_uuid = uuids[:2]
        self.device = device
        self.event: Event = Event()
        self.command_data: bytes | None = None
        self.image_packets: list[int] = []

    @disconnect_on_missing_services
    async def write(self, uuid: str, data: bytes) -> None:
        """청크 분할하여 GATT 쓰기"""
        _LOGGER.debug("Write UUID=%s data=%s", uuid, data.hex())
        for i in range(0, len(data), 20):
            await self.client.write_gatt_char(uuid, data[i : i + 20])
            await sleep(0.05)

    @disconnect_on_missing_services
    async def start_notify(self) -> None:
        """명령 특성에 대한 알림 시작"""
        await self.client.start_notify(self.cmd_uuid, self._notification_handler)
        await sleep(0.5)

    @disconnect_on_missing_services
    async def stop_notify(self) -> None:
        """명령 특성에 대한 알림 중지"""
        await self.client.stop_notify(self.cmd_uuid)

    def _notification_handler(self, _: Any, data: bytearray) -> None:
        """알림 수신 핸들러"""
        self.command_data = bytes(data)
        self.event.set()

    async def read(self, timeout: float = 30.0) -> bytes:
        """알림 대기 후 데이터 반환"""
        await wait_for(self.event.wait(), timeout)
        data = self.command_data or b""
        self.command_data = None
        self.event.clear()
        _LOGGER.debug("Received: %s", data.hex())
        return data

    async def write_cmd(self, uuid, packet: bytes) -> bytes:
        """명령 패킷 쓰기 후 응답 대기"""
        await self.write(uuid, packet)
        return await self.read()

    async def write_image(self, binary: tuple) -> None:
        """이미지 청크 생성 및 전송 상태 머신 실행"""
        _LOGGER.info("이미지 전송 시작")
        self.image_packets = self._make_image_packets(binary)
        try:
            data = await self.write_cmd(self.cmd_uuid, self._make_cmd_packet(0x01))
            while data:
                cmd = data[0]
                if cmd == 0x01:
                    if len(data) < 3 or data[1] != 0xF4 or data[2] != 0x00:
                        break
                    data = await self.write_cmd(self.cmd_uuid, self._make_cmd_packet(0x02))
                elif cmd == 0x02:
                    data = await self.write_cmd(self.cmd_uuid, self._make_cmd_packet(0x03))
                elif cmd == 0x05:
                    if len(data) >= 6 and data[1] == 0x00:
                        part = int.from_bytes(data[2:6], "little")
                        data = await self.write_cmd(self.img_uuid, self._make_img_packet(part))
                    else:
                        break
                else:
                    break
        except Exception as e:
            _LOGGER.error("전송 중 오류: %s", e)
        finally:
            _LOGGER.info("이미지 전송 종료")

    def _make_image_packets(self, binary: tuple) -> list[int]:
        """이미지 바이너리를 EPD 전송용 바이트 패킷 리스트로 변환"""
        image, image_red = binary
        width, height = self.device.resolution
        packets = bytearray()
        channels = (image, image_red) if self.device.red else (image,)
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
        """명령 패킷 생성 (cmd 0x02는 사이즈 포함)"""
        width, height = self.device.resolution
        size = (width * height) // 8 * (2 if self.device.red else 1)
        if cmd == 0x02:
            packet = bytearray(8)
            packet[0] = cmd
            struct.pack_into("<I", packet, 1, size)
            packet[-3:] = b"\x00\x00\x00"
            return bytes(packet)
        return bytes([cmd])

    def _make_img_packet(self, part: int) -> bytes:
        """이미지 청크 패킷 생성 (4바이트 파트 인덱스 + 데이터)"""
        width, height = self.device.resolution
        total = (width * height) // 8 * (2 if self.device.red else 1)
        start = part * 240
        chunk = self.image_packets[start : start + min(240, total - start)]
        packet = bytearray(4 + len(chunk))
        struct.pack_into("<I", packet, 0, part)
        packet[4:] = bytes(chunk)
        return bytes(packet)
