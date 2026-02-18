"""Anyka Talk Integration for Home Assistant."""
import logging
import os

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
CONF_CAM = "cam"
CONF_AUDIO_FILE = "audio_file"
CONF_INPUT_FORMAT = "input_format"

SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_START_TALK = "start_talk"
SERVICE_STOP_TALK = "stop_talk"
SERVICE_START_LISTEN = "start_listen"
SERVICE_STOP_LISTEN = "stop_listen"
SERVICE_UPLOAD_TALK = "upload_talk"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def _validate_target(data):
    """Require camera_ip or cam."""
    if not data.get(CONF_CAMERA_IP) and not data.get(CONF_CAM):
        raise vol.Invalid("camera_ip or cam is required")
    return data


SERVICE_TALK_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_CAMERA_IP): cv.string,
            vol.Optional(CONF_CAM): cv.string,
            vol.Optional(CONF_AUDIO_PORT, default=10000): cv.positive_int,
        }
    ),
    _validate_target,
)

SERVICE_LISTEN_SCHEMA = vol.Schema({vol.Required(CONF_RTSP_URL): cv.string})
SERVICE_UPLOAD_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_CAMERA_IP): cv.string,
            vol.Optional(CONF_CAM): cv.string,
            vol.Required(CONF_AUDIO_FILE): cv.string,
            vol.Optional(CONF_AUDIO_PORT, default=10000): cv.positive_int,
            vol.Optional(CONF_INPUT_FORMAT, default="wav"): cv.string,
        }
    ),
    _validate_target,
)

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
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

    async def handle_start_talk(call: ServiceCall) -> None:
        """Handle start talk service."""
        camera_ip = call.data.get(CONF_CAMERA_IP)
        cam_id = call.data.get(CONF_CAM)
        audio_port = call.data.get(CONF_AUDIO_PORT, 10000)

        try:
            async with session.post(
                f"{addon_url}/api/uplink/start",
                json={CONF_CAMERA_IP: camera_ip, CONF_CAM: cam_id, CONF_AUDIO_PORT: audio_port},
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

    async def _read_audio_file(path: str) -> tuple[bytes, bool]:
        def _reader() -> tuple[bytes, bool]:
            with open(path, "rb") as file_handle:
                data = file_handle.read(MAX_UPLOAD_BYTES)
                return data, bool(file_handle.read(1))

        return await hass.async_add_executor_job(_reader)

    async def handle_upload_talk(call: ServiceCall) -> None:
        """Handle upload talk service."""
        camera_ip = call.data.get(CONF_CAMERA_IP)
        cam_id = call.data.get(CONF_CAM)
        audio_file = call.data.get(CONF_AUDIO_FILE)
        audio_port = call.data.get(CONF_AUDIO_PORT, 10000)
        input_format = call.data.get(CONF_INPUT_FORMAT, "wav")

        try:
            audio_bytes, too_large = await _read_audio_file(audio_file)
            if too_large:
                _LOGGER.error(f"Audio file too large (max {MAX_UPLOAD_BYTES} bytes): {audio_file}")
                return

            form = aiohttp.FormData()
            if camera_ip:
                form.add_field(CONF_CAMERA_IP, camera_ip)
            if cam_id:
                form.add_field(CONF_CAM, cam_id)
            form.add_field(CONF_AUDIO_PORT, str(audio_port))
            form.add_field(CONF_INPUT_FORMAT, input_format)
            form.add_field(
                "audio",
                audio_bytes,
                filename=os.path.basename(audio_file),
                content_type="application/octet-stream",
            )

            async with session.post(f"{addon_url}/api/uplink/upload", data=form) as response:
                if response.status != 200:
                    try:
                        result = await response.json()
                        error_message = result.get("error", "Unknown error")
                    except Exception:
                        error_message = f"HTTP {response.status}"
                    _LOGGER.error("Failed to upload talk: %s", error_message)
        except FileNotFoundError:
            _LOGGER.error("Audio file not found: %s", audio_file)
        except Exception as err:
            _LOGGER.error("Error uploading talk: %s", err)

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
    hass.services.async_register(DOMAIN, SERVICE_UPLOAD_TALK, handle_upload_talk, schema=SERVICE_UPLOAD_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_START_LISTEN, handle_start_listen, schema=SERVICE_LISTEN_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP_LISTEN, handle_stop_listen)
    hass.services.async_register(DOMAIN, SERVICE_START, handle_start_talk, schema=SERVICE_TALK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop_talk)

    async def _close_session(_):
        await session.close()

    hass.bus.async_listen_once("homeassistant_stop", _close_session)
    return True
