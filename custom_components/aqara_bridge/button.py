"""Button entities for Aqara virtual infrared remotes."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo

from .core.aiot_manager import AiotDevice, AiotManager, VIRTUAL_IR_MODELS
from .core.const import DOMAIN, HASS_DATA_AIOT_MANAGER


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Create one clickable entity for every cloud infrared key."""
    manager: AiotManager = hass.data[DOMAIN][HASS_DATA_AIOT_MANAGER]
    entities = []
    for device in manager.devices_for_entry(config_entry):
        if device.model not in VIRTUAL_IR_MODELS:
            continue
        try:
            commands = await manager.async_get_ir_commands(device)
        except Exception:
            continue
        entities.extend(
            AqaraIrCommandButton(manager, device, name, key_id)
            for name, key_id in commands.items()
        )
    async_add_entities(entities)


class AqaraIrCommandButton(ButtonEntity):
    """Send one command from an Aqara virtual infrared remote."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:remote"

    def __init__(
        self,
        manager: AiotManager,
        device: AiotDevice,
        command_name: str,
        key_id: str,
    ):
        self._manager = manager
        self._device = device
        self._key_id = key_id
        self._attr_name = command_name
        self._attr_unique_id = (
            f"{DOMAIN}.ir_button_{device.did}_{key_id}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.did)},
            name=device.device_name,
            model=device.model,
            manufacturer=device.manufacturer,
            sw_version=device.firmware_version,
            hw_version=device.heard_version,
            suggested_area=device.position_name,
        )

    async def async_press(self) -> None:
        """Send the infrared key through Aqara Cloud."""
        await self._manager.session.async_click_ir_key(
            self._device.did, self._key_id
        )
