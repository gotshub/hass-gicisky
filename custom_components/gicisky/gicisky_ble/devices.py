import dataclasses


@dataclasses.dataclass
class DeviceEntry:
    name: str
    model: str
    resolution: tuple
    red: bool = True
    manufacturer: str = "Gicisky"
    max_voltage: float = 2.9
    min_voltage: float = 2.9



    # 0x0B: "GICI_BLE_EPD_21_BWR",
    # 0x28: "GICI_BLE_EPD_29_BW",
    # 0x30: "GICI_BLE_EPD_29_BW",
    # 0x2B: "GICI_BLE_EPD_29_BWR",
    # 0x33: "GICI_BLE_EPD_29_BWR1",
    # 0x48: "GICI_BLE_EPD_BW_42",
    # 0x4B: "GICI_BLE_EPD_BWR_42",
    # 0x40: "GICI_BLE_TFT_BW_42",
    # 0x42: "GICI_BLE_TFT_BWR_42",
    # 0x68: "GICI_BLE_EPD_BW_74",
    # 0x6A: "GICI_BLE_EPD_BWR_74",
    # 0xEB: "GICI_BLE_EPD_BWR_29_SILABS",



    # 0x0B: (250, 128),  # GICI_BLE_EPD_21_BWR
    # 0x28: (296, 128),  # GICI_BLE_EPD_29_BW  (2.9��ġ, 296 �� 128 �ȼ�)
    # 0x30: (296, 128),  # GICI_BLE_EPD_29_BW
    # 0x2B: (296, 128),  # GICI_BLE_EPD_29_BWR
    # 0x33: (296, 128),  # GICI_BLE_EPD_29_BWR1
    # 0x48: (400, 300),  # GICI_BLE_EPD_BW_42  (4.2��ġ, 400 �� 300 �ȼ�)
    # 0x4B: (400, 300),  # GICI_BLE_EPD_BWR_42
    # 0x40: (400, 300),  # GICI_BLE_TFT_BW_42
    # 0x42: (400, 300),  # GICI_BLE_TFT_BWR_42
    # 0x68: (800, 480),  # GICI_BLE_EPD_BW_74  (7.4��ġ, 800 �� 480 �ȼ�)
    # 0x6A: (800, 480),  # GICI_BLE_EPD_BWR_74
    # 0xEB: (296, 128),  # GICI_BLE_EPD_BWR_29_SILABS (2.9��ġ)

DEVICE_TYPES: dict[int, DeviceEntry] = {
    0xA0: DeviceEntry(
        name="TFT 21",
        model="TFT 21 BW",
        resolution=(250, 132),
        red=False
    ),
    0x0B: DeviceEntry(
        name="EPD 21",
        model="EPD 21 BWR",
        resolution=(250, 128),
    ),
    0x32: DeviceEntry(
        name="EPD 29",
        model="EPD 29 BWR",
        resolution=(296, 128),
    ),
    0x4B: DeviceEntry(
        name="EPD 42",
        model="EPD 42 BWR",
        resolution=(400, 300),
        max_voltage=3.0
    ),

}
