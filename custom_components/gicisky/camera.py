
import logging
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN
from .coordinator import GiciskyPassiveBluetoothProcessorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gicisky camera."""
    coordinator: GiciskyPassiveBluetoothProcessorCoordinator = entry.runtime_data
    async_add_entities([GiciskyCamera(coordinator)])


class GiciskyCamera(Camera):
    """Gicisky Camera."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_supported_features = CameraEntityFeature.ON_OFF

    def __init__(self, coordinator: GiciskyPassiveBluetoothProcessorCoordinator) -> None:
        """Initialize the camera."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.address}_displayed_content"
        # Use the same device info pattern as event entities to ensure proper device association
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            connections={(dr.CONNECTION_BLUETOOTH, coordinator.address)},
        )
        self._attr_name = "Displayed content"
        self._attr_is_on = False
        self._image = None

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the camera image."""
        return self._image

    def set_image(self, image: bytes):
        """Set the image."""
        self._image = image
        self._attr_is_on = True
        self.async_write_ha_state()

    def turn_off(self) -> None:
        """Turn the camera off."""
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self._attr_device_info

    @property
    def name(self) -> str:
        """Return the name."""
        return self._attr_name
