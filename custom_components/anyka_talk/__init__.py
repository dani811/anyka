"""Anyka Two-Way Audio Integration."""
import logging
import aiohttp
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "anyka_talk"
APPDAEMON_URL = "http://localhost:5050"

SERVICE_START = "start"
SERVICE_STOP = "stop"

SERVICE_START_SCHEMA = vol.Schema({
    vol.Required("camera_ip"): cv.string,
})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Anyka Talk component."""
    
    session = aiohttp.ClientSession()
    
    async def handle_start(call: ServiceCall) -> None:
        """Handle the start service call."""
        camera_ip = call.data.get("camera_ip")
        _LOGGER.info("Starting Anyka audio stream to %s", camera_ip)
        
        try:
            async with session.post(
                f"{APPDAEMON_URL}/start",
                json={"camera_ip": camera_ip}
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Audio stream started successfully")
                else:
                    _LOGGER.error("Failed to start audio stream: %s", response.status)
        except Exception as e:
            _LOGGER.error("Error starting audio stream: %s", e)
    
    async def handle_stop(call: ServiceCall) -> None:
        """Handle the stop service call."""
        _LOGGER.info("Stopping Anyka audio stream")
        
        try:
            async with session.post(f"{APPDAEMON_URL}/stop") as response:
                if response.status == 200:
                    _LOGGER.info("Audio stream stopped successfully")
                else:
                    _LOGGER.error("Failed to stop audio stream: %s", response.status)
        except Exception as e:
            _LOGGER.error("Error stopping audio stream: %s", e)
    
    hass.services.async_register(DOMAIN, SERVICE_START, handle_start, schema=SERVICE_START_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
    
    return True
