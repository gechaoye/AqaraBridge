from homeassistant.components.event import EventEntity

from .core.aiot_manager import (
    AiotManager,
    AiotEntityBase,
)
from .core.const import (
    BUTTON,
    CUBE,
    DOMAIN,
    HASS_DATA_AIOT_MANAGER,
    GESTURE_MAPPING,
    PET_MAPPING,
    HUMAN_MAPPING,
    MOVING_MAPPING,
    SOUND_MAPPING,
)
import logging

_LOGGER = logging.getLogger(__name__)

TYPE = "event"

DATA_KEY = f"{TYPE}.{DOMAIN}"


async def async_setup_entry(hass, config_entry, async_add_entities):
    manager: AiotManager = hass.data[DOMAIN][HASS_DATA_AIOT_MANAGER]
    cls_entities = {
        "default": AiotEventEntity,
        "button": AiotButtonEntity,
        "camera": AiotCameraEntity,
        "lock_event": AiotLockEventEntity,
        "inside_unlock": AiotLockEventEntity,
        "fingerprint_unlock": AiotLockEventEntity,
        "password_unlock": AiotLockEventEntity,
        "nfc_unlock": AiotLockEventEntity,
        "temporary_password_unlock": AiotLockEventEntity,
    }
    await manager.async_add_entities(
        config_entry, TYPE, cls_entities, async_add_entities
    )


class AiotEventEntity(AiotEntityBase, EventEntity):
    def __init__(self, hass, device, res_params, channel=None, **kwargs):
        AiotEntityBase.__init__(self, hass, device, res_params, TYPE, channel, **kwargs)
        mapping = kwargs.get("event_mapping")
        self._attr_event_types = list(dict.fromkeys(mapping.values()))
        self.event_mapping = mapping
        icon = kwargs.get("icon")
        if icon:
            self._attr_icon = icon
        self._extra_state_attributes.extend(["trigger_time", "trigger_dt"])

    @property
    def icon(self):
        return "mdi:button-pointer"

    async def async_update(self):
        """Wait for real-time events instead of querying a pulse resource."""

    def convert_res_to_attr(self, res_name, res_value):
        if res_name == "event":
            trigger = self.event_mapping.get(res_value, "unknown")
            self._trigger_event(trigger)
            self.schedule_update_ha_state()
        return super().convert_res_to_attr(res_name, res_value)


class AiotButtonEntity(AiotEntityBase, EventEntity):
    def __init__(self, hass, device, res_params, channel=None, **kwargs):
        AiotEntityBase.__init__(self, hass, device, res_params, TYPE, channel, **kwargs)
        self._attr_event_types = list(BUTTON.values())
        self._extra_state_attributes.extend(["trigger_time", "trigger_dt"])

    @property
    def icon(self):
        """return icon."""
        return "mdi:button-pointer"

    async def async_update(self):
        """Wait for real-time events instead of querying a pulse resource."""

    def convert_res_to_attr(self, res_name, res_value):
        if res_name == "firmware_version":
            return res_value
        if res_name == "zigbee_lqi":
            return int(res_value)
        if res_name == "button" and res_value not in (0, ""):
            trigger = BUTTON.get(res_value, "unknown")
            self._trigger_event(trigger)
            self.schedule_update_ha_state()
        return super().convert_res_to_attr(res_name, res_value)


class AiotLockEventEntity(AiotEntityBase, EventEntity):
    """An event emitted by an Aqara smart lock."""

    def __init__(self, hass, device, res_params, channel=None, **kwargs):
        AiotEntityBase.__init__(self, hass, device, res_params, TYPE, channel, **kwargs)
        self._attr_event_types = ["triggered"]
        self._extra_state_attributes.extend(["trigger_time", "trigger_dt"])

    async def async_update(self):
        """Wait for real-time lock events instead of replaying the latest value."""

    def convert_res_to_attr(self, res_name, res_value):
        self._trigger_event("triggered", {"value": res_value})
        self.schedule_update_ha_state()
        return res_value


class AiotCameraEntity(AiotEntityBase, EventEntity):
    def __init__(self, hass, device, res_params, channel=None, **kwargs):
        AiotEntityBase.__init__(self, hass, device, res_params, TYPE, channel, **kwargs)
        self._extra_state_attributes.extend(["trigger_time", "trigger_dt"])
        event_types = kwargs.get("event_types")
        event_types_mapping = kwargs.get("event_types_mapping")
        if event_types:
            self._attr_event_types = event_types
        if event_types_mapping:
            self._attr_event_types = list(event_types_mapping.values())

    @property
    def icon(self):
        """return icon."""
        return "mdi:alarm-light-outline"

    async def async_update(self):
        """Wait for real-time events instead of replaying the latest value."""

    def convert_res_to_attr(self, res_name, res_value):
        if res_name == "detect_face_event" and res_value not in (0, ""):
            self._trigger_event(res_value)
        if res_name == "detect_human_event" and res_value not in (0, ""):
            self._trigger_event(HUMAN_MAPPING.get(res_value, "unknown"))
        if res_name == "detect_pets_event" and res_value not in (0, ""):
            self._trigger_event(PET_MAPPING.get(res_value, "unknown"))
        if res_name == "detect_gesture_event" and res_value not in (0, ""):
            self._trigger_event(GESTURE_MAPPING.get(res_value, "unknown"))
        if res_name == "detect_moving_event" and res_value not in (0, ""):
            self._trigger_event(MOVING_MAPPING.get(res_value, "unknown"))
        if res_name == "detect_sound_event" and res_value not in (0, ""):
            self._trigger_event(SOUND_MAPPING.get(res_value, "unknown"))
        self.schedule_update_ha_state()
        return super().convert_res_to_attr(res_name, res_value)
