"""Anyka Talk Integration for Home Assistant."""
import logging

import aiohttp
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "anyka_talk"
DEFAULT_PORT = 8099

CONF_CAMERA_IP = "camera_ip"
CONF_RTSP_URL = "rtsp_url"
CONF_AUDIO_PORT = "audio_port"

SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_START_TALK = "start_talk"
SERVICE_STOP_TALK = "stop_talk"
SERVICE_START_LISTEN = "start_listen"
SERVICE_STOP_LISTEN = "stop_listen"

SERVICE_TALK_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CAMERA_IP): cv.string,
        vol.Optional(CONF_AUDIO_PORT, default=10000): cv.positive_int,
    }
)

SERVICE_LISTEN_SCHEMA = vol.Schema({vol.Required(CONF_RTSP_URL): cv.string})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default="localhost"): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Anyka Talk component."""
    conf = config.get(DOMAIN, {})
    addon_host = conf.get(CONF_HOST, "localhost")
    addon_port = conf.get(CONF_PORT, DEFAULT_PORT)
    addon_url = f"http://{addon_host}:{addon_port}"
    session = aiohttp.ClientSession()

    async def handle_start_talk(call: ServiceCall) -> None:
        """Handle start talk service."""
        camera_ip = call.data.get(CONF_CAMERA_IP)
        audio_port = call.data.get(CONF_AUDIO_PORT, 10000)

        try:
            async with session.post(
                f"{addon_url}/api/uplink/start",
                json={CONF_CAMERA_IP: camera_ip, CONF_AUDIO_PORT: audio_port},
            ) as response:
                if response.status != 200:
                    result = await response.json()
                    _LOGGER.error("Failed to start talk: %s", result.get("error", "Unknown error"))
        except Exception as err:
            _LOGGER.error("Error starting talk: %s", err)

    async def handle_stop_talk(call: ServiceCall) -> None:
        """Handle stop talk service."""
        try:
            async with session.post(f"{addon_url}/api/uplink/stop") as response:
                if response.status != 200:
                    result = await response.json()
                    _LOGGER.error("Failed to stop talk: %s", result.get("error", "Unknown error"))
        except Exception as err:
            _LOGGER.error("Error stopping talk: %s", err)

    async def handle_start_listen(call: ServiceCall) -> None:
        """Handle start listen service."""
        rtsp_url = call.data.get(CONF_RTSP_URL)

        try:
            async with session.post(
                f"{addon_url}/api/downlink/start",
                json={CONF_RTSP_URL: rtsp_url},
            ) as response:
                if response.status != 200:
                    result = await response.json()
                    _LOGGER.error("Failed to start listen: %s", result.get("error", "Unknown error"))
        except Exception as err:
            _LOGGER.error("Error starting listen: %s", err)

    async def handle_stop_listen(call: ServiceCall) -> None:
        """Handle stop listen service."""
        try:
            async with session.post(f"{addon_url}/api/downlink/stop") as response:
                if response.status != 200:
                    result = await response.json()
                    _LOGGER.error("Failed to stop listen: %s", result.get("error", "Unknown error"))
        except Exception as err:
            _LOGGER.error("Error stopping listen: %s", err)

    hass.services.async_register(DOMAIN, SERVICE_START_TALK, handle_start_talk, schema=SERVICE_TALK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP_TALK, handle_stop_talk)
    hass.services.async_register(DOMAIN, SERVICE_START_LISTEN, handle_start_listen, schema=SERVICE_LISTEN_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP_LISTEN, handle_stop_listen)
    hass.services.async_register(DOMAIN, SERVICE_START, handle_start_talk, schema=SERVICE_TALK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop_talk)

    async def _close_session(_event):
        await session.close()

    hass.bus.async_listen_once("homeassistant_stop", _close_session)
    return True
