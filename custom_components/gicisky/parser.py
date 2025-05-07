from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

class BLEDataParser:

    def __init__(self):
        # 초기화가 필요하면 여기에
        pass

    def update(self, service_info: BluetoothServiceInfoBleak) -> dict:
        """Advertisement가 들어올 때마다 호출됩니다."""
        # 예: 특정 manufacturer ID의 raw bytes
        # raw = service_info.manufacturer_data.get(0xFFFF)
        # if not raw:
        #     return {}

        battery = 100

        return {
            "battery": battery,
        }
