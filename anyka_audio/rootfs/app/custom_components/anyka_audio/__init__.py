"""Anyka Bidirectional Audio Integration for Home Assistant."""
import logging
import aiohttp
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_HOST, CONF_PORT

_LOGGER = logging.getLogger(__name__)

DOMAIN = "anyka_audio"
DEFAULT_PORT = 8099

CONF_CAMERA_IP = "camera_ip"
CONF_RTSP_URL = "rtsp_url"
CONF_AUDIO_PORT = "audio_port"

# Services
SERVICE_START_TALK = "start_talk"
SERVICE_STOP_TALK = "stop_talk"
SERVICE_START_LISTEN = "start_listen"
SERVICE_STOP_LISTEN = "stop_listen"

SERVICE_TALK_SCHEMA = vol.Schema({
    vol.Required(CONF_CAMERA_IP): cv.string,
    vol.Optional(CONF_AUDIO_PORT, default=10000): cv.positive_int,
})

SERVICE_LISTEN_SCHEMA = vol.Schema({
    vol.Required(CONF_RTSP_URL): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_HOST, default="localhost"): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Anyka Audio component."""
    
    conf = config.get(DOMAIN, {})
    addon_host = conf.get(CONF_HOST, "localhost")
    addon_port = conf.get(CONF_PORT, DEFAULT_PORT)
    addon_url = f"http://{addon_host}:{addon_port}"
    
    _LOGGER.info("Setting up Anyka Audio integration (addon: %s)", addon_url)
    
    session = aiohttp.ClientSession()
    
    async def handle_start_talk(call: ServiceCall) -> None:
        """Handle start talk service."""
        camera_ip = call.data.get(CONF_CAMERA_IP)
        audio_port = call.data.get(CONF_AUDIO_PORT, 10000)
        
        _LOGGER.info("Starting talk to camera %s:%s", camera_ip, audio_port)
        
        try:
            async with session.post(
                f"{addon_url}/api/uplink/start",
                json={"camera_ip": camera_ip, "audio_port": audio_port}
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Talk started successfully")
                else:
                    result = await response.json()
                    _LOGGER.error("Failed to start talk: %s", result.get('error', 'Unknown error'))
        except Exception as e:
            _LOGGER.error("Error starting talk: %s", e)
    
    async def handle_stop_talk(call: ServiceCall) -> None:
        """Handle stop talk service."""
        _LOGGER.info("Stopping talk")
        
        try:
            async with session.post(f"{addon_url}/api/uplink/stop") as response:
                if response.status == 200:
                    _LOGGER.info("Talk stopped successfully")
                else:
                    result = await response.json()
                    _LOGGER.error("Failed to stop talk: %s", result.get('error', 'Unknown error'))
        except Exception as e:
            _LOGGER.error("Error stopping talk: %s", e)
    
    async def handle_start_listen(call: ServiceCall) -> None:
        """Handle start listen service."""
        rtsp_url = call.data.get(CONF_RTSP_URL)
        
        _LOGGER.info("Starting listen from RTSP: %s", rtsp_url)
        
        try:
            async with session.post(
                f"{addon_url}/api/downlink/start",
                json={"rtsp_url": rtsp_url}
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Listen started successfully")
                else:
                    result = await response.json()
                    _LOGGER.error("Failed to start listen: %s", result.get('error', 'Unknown error'))
        except Exception as e:
            _LOGGER.error("Error starting listen: %s", e)
    
    async def handle_stop_listen(call: ServiceCall) -> None:
        """Handle stop listen service."""
        _LOGGER.info("Stopping listen")
        
        try:
            async with session.post(f"{addon_url}/api/downlink/stop") as response:
                if response.status == 200:
                    _LOGGER.info("Listen stopped successfully")
                else:
                    result = await response.json()
                    _LOGGER.error("Failed to stop listen: %s", result.get('error', 'Unknown error'))
        except Exception as e:
            _LOGGER.error("Error stopping listen: %s", e)
    
    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_START_TALK, handle_start_talk, schema=SERVICE_TALK_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_TALK, handle_stop_talk
    )
    hass.services.async_register(
        DOMAIN, SERVICE_START_LISTEN, handle_start_listen, schema=SERVICE_LISTEN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_LISTEN, handle_stop_listen
    )
    
    return True
