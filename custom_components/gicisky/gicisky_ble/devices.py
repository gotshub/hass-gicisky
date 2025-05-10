import dataclasses


@dataclasses.dataclass
class DeviceEntry:
    name: str
    model: str
    resolution: tuple
    red: bool = True
    manufacturer: str = "Gicisky"
    max_voltage: float = 2.9
    min_voltage: float = 2.2

DEVICE_TYPES: dict[int, DeviceEntry] = {
    0xA0: DeviceEntry(
        name="TFT 21",
        model="TFT 2.1\" BW",
        resolution=(250, 132),
        red=False
    ),
    0x0B: DeviceEntry(
        name="EPD 21",
        model="EPD 2.1\" BWR",
        resolution=(250, 128),
    ),
    0x32: DeviceEntry(
        name="EPD 29",
        model="EPD 2.9\" BWR",
        resolution=(296, 128),
    ),
    0x4B: DeviceEntry(
        name="EPD 42",
        model="EPD 4.2\" BWR",
        resolution=(400, 300),
        max_voltage=3.0
    ),

}
