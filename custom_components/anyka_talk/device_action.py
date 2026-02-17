"""Device actions for Anyka Talk."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv

from . import (
    CONF_AUDIO_PORT,
    CONF_AUDIO_FILE,
    CONF_CAMERA_IP,
    CONF_INPUT_FORMAT,
    CONF_RTSP_URL,
    DOMAIN,
    SERVICE_START_LISTEN,
    SERVICE_START_TALK,
    SERVICE_STOP_LISTEN,
    SERVICE_STOP_TALK,
    SERVICE_UPLOAD_TALK,
)

ACTION_TYPES = {
    SERVICE_START_TALK,
    SERVICE_STOP_TALK,
    SERVICE_START_LISTEN,
    SERVICE_STOP_LISTEN,
    SERVICE_UPLOAD_TALK,
}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_DOMAIN): DOMAIN,
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Optional(CONF_CAMERA_IP): cv.string,
        vol.Optional(CONF_AUDIO_PORT): cv.positive_int,
        vol.Optional(CONF_RTSP_URL): cv.string,
        vol.Optional(CONF_AUDIO_FILE): cv.string,
        vol.Optional(CONF_INPUT_FORMAT): cv.string,
    }
)


async def async_validate_action_config(
    hass: HomeAssistant, config: dict
) -> dict:
    """Validate device action config."""
    config = ACTION_SCHEMA(config)
    action_type = config[CONF_TYPE]
    if action_type == SERVICE_START_TALK and CONF_CAMERA_IP not in config:
        raise vol.Invalid("Camera IP is required for start_talk")
    if action_type == SERVICE_UPLOAD_TALK and (CONF_CAMERA_IP not in config or CONF_AUDIO_FILE not in config):
        raise vol.Invalid("Camera IP and audio file are required for upload_talk")
    if action_type == SERVICE_START_LISTEN and CONF_RTSP_URL not in config:
        raise vol.Invalid("RTSP URL is required for start_listen")
    return config


async def async_get_actions(hass: HomeAssistant, device_id: str) -> list[dict]:
    """List device actions."""
    base = {
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }
    return [
        {**base, CONF_TYPE: SERVICE_START_TALK},
        {**base, CONF_TYPE: SERVICE_STOP_TALK},
        {**base, CONF_TYPE: SERVICE_START_LISTEN},
        {**base, CONF_TYPE: SERVICE_STOP_LISTEN},
        {**base, CONF_TYPE: SERVICE_UPLOAD_TALK},
    ]


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict[str, Any], _variables: dict[str, Any], context: Context
) -> None:
    """Execute a configured device action."""
    service = config[CONF_TYPE]
    data: dict[str, Any] = {}

    if service == SERVICE_START_TALK:
        data[CONF_CAMERA_IP] = config[CONF_CAMERA_IP]
        if CONF_AUDIO_PORT in config:
            data[CONF_AUDIO_PORT] = config[CONF_AUDIO_PORT]
    elif service == SERVICE_UPLOAD_TALK:
        data[CONF_CAMERA_IP] = config[CONF_CAMERA_IP]
        data[CONF_AUDIO_FILE] = config[CONF_AUDIO_FILE]
        if CONF_AUDIO_PORT in config:
            data[CONF_AUDIO_PORT] = config[CONF_AUDIO_PORT]
        if CONF_INPUT_FORMAT in config:
            data[CONF_INPUT_FORMAT] = config[CONF_INPUT_FORMAT]
    elif service == SERVICE_START_LISTEN:
        data[CONF_RTSP_URL] = config[CONF_RTSP_URL]

    await hass.services.async_call(
        DOMAIN,
        service,
        data,
        blocking=True,
        context=context,
    )


async def async_get_action_capabilities(
    hass: HomeAssistant, config: dict
) -> dict:
    """List action fields shown in UI."""
    action_type = config[CONF_TYPE]
    if action_type == SERVICE_START_TALK:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(CONF_CAMERA_IP): cv.string,
                    vol.Optional(CONF_AUDIO_PORT, default=10000): cv.positive_int,
                }
            )
        }
    if action_type == SERVICE_UPLOAD_TALK:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(CONF_CAMERA_IP): cv.string,
                    vol.Required(CONF_AUDIO_FILE): cv.string,
                    vol.Optional(CONF_AUDIO_PORT, default=10000): cv.positive_int,
                    vol.Optional(CONF_INPUT_FORMAT, default="wav"): cv.string,
                }
            )
        }
    if action_type == SERVICE_START_LISTEN:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(CONF_RTSP_URL): cv.string,
                }
            )
        }
    return {"extra_fields": vol.Schema({})}
