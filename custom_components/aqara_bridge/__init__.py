import datetime
from email import message
import re
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.event import async_track_point_in_time

from .core.aiot_manager import (
    AiotManager,
    AiotDevice,
)
from .core.aiot_cloud import AiotCloud
from .core.const import *


_LOGGER = logging.getLogger(__name__)

_DEBUG_ACCESSTOKEN = ""
_DEBUG_REFRESHTOEEN = ""
_DEBUG_STATUS = False
TOKEN_REFRESH_ADVANCE = datetime.timedelta(days=3)
TOKEN_REFRESH_RETRY_DELAY = datetime.timedelta(hours=1)
TOKEN_EXPIRY_UNKNOWN = datetime.datetime.min.replace(tzinfo=datetime.UTC)


def data_masking(s: str, n: int) -> str:
    return re.sub(f"(?<=.{{{n}}}).(?=.{{{n}}})", "*", str(s))


def gen_auth_entry(
    app_id: str,
    app_key: str,
    key_id: str,
    account: str,
    account_type: int,
    country_code: str,
    token_result: dict,
):
    auth_entry = {}
    auth_entry[CONF_ENTRY_APP_ID] = app_id
    auth_entry[CONF_ENTRY_APP_KEY] = app_key
    auth_entry[CONF_ENTRY_KEY_ID] = key_id
    auth_entry[CONF_ENTRY_AUTH_ACCOUNT] = account
    auth_entry[CONF_ENTRY_AUTH_ACCOUNT_TYPE] = account_type
    auth_entry[CONF_ENTRY_AUTH_COUNTRY_CODE] = country_code
    return update_auth_entry_tokens(auth_entry, token_result)


def update_auth_entry_tokens(auth_entry: dict, token_result: dict) -> dict:
    """Return config entry data updated with a complete token response."""
    data = auth_entry.copy()
    data[CONF_ENTRY_AUTH_ACCESS_TOKEN] = token_result["accessToken"]
    data[CONF_ENTRY_AUTH_REFRESH_TOKEN] = token_result["refreshToken"]

    if open_id := token_result.get("openId"):
        data[CONF_ENTRY_AUTH_OPENID] = open_id

    if expires_in := token_result.get("expiresIn"):
        data[CONF_ENTRY_AUTH_EXPIRES_IN] = expires_in
        data[CONF_ENTRY_AUTH_EXPIRES_TIME] = (
            datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=int(expires_in))
        ).strftime("%Y-%m-%d %H:%M:%S")

    return data


def config_signature(entry: ConfigEntry) -> dict:
    """Return the non-token config that requires an integration reload."""
    data = entry.data
    return {
        CONF_ENTRY_APP_ID: data.get(CONF_ENTRY_APP_ID),
        CONF_ENTRY_APP_KEY: data.get(CONF_ENTRY_APP_KEY),
        CONF_ENTRY_KEY_ID: data.get(CONF_ENTRY_KEY_ID),
        CONF_ENTRY_AUTH_ACCOUNT: data.get(CONF_ENTRY_AUTH_ACCOUNT),
        CONF_ENTRY_AUTH_ACCOUNT_TYPE: data.get(CONF_ENTRY_AUTH_ACCOUNT_TYPE),
        CONF_ENTRY_AUTH_COUNTRY_CODE: data.get(CONF_ENTRY_AUTH_COUNTRY_CODE),
        "options": dict(entry.options),
    }


def parse_token_expiry(expires_datetime: str | None) -> datetime.datetime:
    """Parse the Aqara token expiry time stored as UTC."""
    if expires_datetime:
        try:
            return datetime.datetime.strptime(
                expires_datetime, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=datetime.UTC)
        except (TypeError, ValueError):
            pass
    return TOKEN_EXPIRY_UNKNOWN


def token_refresh_time(expires_at: datetime.datetime) -> datetime.datetime:
    """Return the proactive refresh time before expiration."""
    return expires_at - TOKEN_REFRESH_ADVANCE


def init_hass_data(hass):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(HASS_DATA_AUTH_ENTRY_ID, None)
    session = AiotCloud(aiohttp_client.async_create_clientsession(hass))
    if not hass.data[DOMAIN].get(HASS_DATA_AIOTCLOUD):
        hass.data[DOMAIN].setdefault(HASS_DATA_AIOTCLOUD, session)
    if not hass.data[DOMAIN].get(HASS_DATA_AIOT_MANAGER):
        hass.data[DOMAIN].setdefault(HASS_DATA_AIOT_MANAGER, AiotManager(hass, session))


async def async_setup(hass, config):
    """Setup component."""
    init_hass_data(hass)
    return True


async def async_setup_entry(hass, entry):
    data = entry.data.copy()
    if _DEBUG_STATUS:
        import time

        data[CONF_ENTRY_AUTH_REFRESH_TOKEN] = _DEBUG_REFRESHTOEEN
        data[CONF_ENTRY_AUTH_ACCESS_TOKEN] = _DEBUG_ACCESSTOKEN
        data[CONF_ENTRY_AUTH_EXPIRES_TIME] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 24 * 3600)
        )

    manager: AiotManager = hass.data[DOMAIN][HASS_DATA_AIOT_MANAGER]
    aiotcloud: AiotCloud = hass.data[DOMAIN][HASS_DATA_AIOTCLOUD]

    def cancel_token_refresh_timer():
        if unsubscribe := hass.data[DOMAIN].pop(
            HASS_DATA_TOKEN_REFRESH_UNSUB, None
        ):
            unsubscribe()

    def schedule_token_refresh_at(refresh_at: datetime.datetime):
        cancel_token_refresh_timer()

        async def refresh_token(_now):
            hass.data[DOMAIN].pop(HASS_DATA_TOKEN_REFRESH_UNSUB, None)
            if not aiotcloud.refresh_token:
                _LOGGER.error("Unable to refresh Aqara token: refresh token is missing")
                return

            resp = await aiotcloud.async_refresh_token(aiotcloud.refresh_token)
            if not isinstance(resp, dict) or resp.get("code") != 0:
                retry_at = (
                    datetime.datetime.now(datetime.UTC) + TOKEN_REFRESH_RETRY_DELAY
                )
                _LOGGER.error(
                    "Unable to refresh Aqara token; retrying at %s", retry_at
                )
                schedule_token_refresh_at(retry_at)

        hass.data[DOMAIN][HASS_DATA_TOKEN_REFRESH_UNSUB] = (
            async_track_point_in_time(hass, refresh_token, refresh_at)
        )

    def schedule_token_refresh(expires_at: datetime.datetime):
        schedule_token_refresh_at(token_refresh_time(expires_at))

    def token_updated(token_result):
        auth_entry = hass.data[DOMAIN][HASS_DATA_AUTH_ENTRY_ID]
        if auth_entry:
            updated_data = update_auth_entry_tokens(auth_entry.data, token_result)
            hass.config_entries.async_update_entry(auth_entry, data=updated_data)
            expires_at = parse_token_expiry(
                updated_data.get(CONF_ENTRY_AUTH_EXPIRES_TIME)
            )
            if expires_at != TOKEN_EXPIRY_UNKNOWN:
                schedule_token_refresh(expires_at)

    aiotcloud.set_options(entry.options)
    aiotcloud.set_app_id(data[CONF_ENTRY_APP_ID])
    aiotcloud.set_app_key(data[CONF_ENTRY_APP_KEY])
    aiotcloud.set_key_id(data[CONF_ENTRY_KEY_ID])
    aiotcloud.set_country(data[CONF_ENTRY_AUTH_COUNTRY_CODE])
    aiotcloud.access_token = data.get(CONF_ENTRY_AUTH_ACCESS_TOKEN)
    aiotcloud.refresh_token = data.get(CONF_ENTRY_AUTH_REFRESH_TOKEN)
    aiotcloud.update_token_event_callback = token_updated
    hass.data[DOMAIN][HASS_DATA_AUTH_ENTRY_ID] = entry

    expires_at = parse_token_expiry(data.get(CONF_ENTRY_AUTH_EXPIRES_TIME))
    refresh_at = token_refresh_time(expires_at)
    if expires_at == TOKEN_EXPIRY_UNKNOWN:
        _LOGGER.warning("Invalid Aqara token expiry time; refreshing token")

    if refresh_at <= datetime.datetime.now(datetime.UTC):
        if not aiotcloud.refresh_token:
            _LOGGER.error("Unable to refresh Aqara token: refresh token is missing")
            return False
        resp = await aiotcloud.async_refresh_token(aiotcloud.refresh_token)
        if not isinstance(resp, dict) or resp.get("code") != 0:
            _LOGGER.error("Unable to proactively refresh Aqara token")
            return False
    else:
        schedule_token_refresh_at(refresh_at)

    hass.data[DOMAIN][HASS_DATA_CONFIG_SIGNATURE] = config_signature(entry)
    entry.async_on_unload(cancel_token_refresh_timer)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    if manager._msg_handler is not None:
        # 如果重新配置，重新启动mq
        manager._msg_handler.stop()
    await manager.start_msg_hanlder(
        data[CONF_ENTRY_APP_ID], data[CONF_ENTRY_APP_KEY], data[CONF_ENTRY_KEY_ID]
    )
    if len(manager.all_devices) == 0:
        await manager.async_add_all_devices(entry)
        await manager.async_forward_entry_setup(entry)
    else:
        await manager.async_add_all_devices(entry)

    return True


async def async_unload_entry(hass, entry):
    # if CONF_ENTRY_AUTH_ACCOUNT in entry.data:
    #     hass.data[DOMAIN][HASS_DATA_AUTH_ENTRY_ID] = None
    # else:
    #     manager: AiotManager = hass.data[DOMAIN][HASS_DATA_AIOT_MANAGER]
    #     await manager.async_unload_entry(entry)
    return True


async def async_remove_entry(hass, entry):
    if CONF_ENTRY_AUTH_ACCOUNT in entry.data:
        hass.data[DOMAIN][HASS_DATA_AUTH_ENTRY_ID] = None
    else:
        manager: AiotManager = hass.data[DOMAIN][HASS_DATA_AIOT_MANAGER]
        await manager.async_remove_entry(entry)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Reload when non-token configuration changes."""
    if hass.data[DOMAIN].get(HASS_DATA_CONFIG_SIGNATURE) == config_signature(entry):
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""
    return True
