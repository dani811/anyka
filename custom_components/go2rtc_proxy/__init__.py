"""Proxy autenticado de Home Assistant hacia la API de go2rtc.

Advanced Camera Card solo ofrece pulsar-para-hablar con su proveedor `go2rtc`, que
abre `<url>/api/ws?src=<stream>` desde el navegador. go2rtc escucha en HTTP y sin
contraseña, así que una página HTTPS no puede usarlo directamente. Con
`go2rtc.url: /api/go2rtc_proxy` la card firma la ruta con HA (`authSig`) y este
proxy reenvía la petición al go2rtc local: mismo origen HTTPS, solo usuarios de HA.
"""

from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiohttp import web
import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "go2rtc_proxy"
CONF_URL = "url"
DEFAULT_URL = "http://localhost:1984"
BASE_PATH = f"/api/{DOMAIN}/api"

# Solo los parámetros que usa la card; nunca reenviamos authSig ni otros.
ALLOWED_QUERY = ("src", "video", "audio", "media")

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Optional(CONF_URL, default=DEFAULT_URL): cv.url})},
    extra=vol.ALLOW_EXTRA,
)


def _query(request: web.Request) -> dict[str, str]:
    return {k: request.query[k] for k in ALLOWED_QUERY if k in request.query}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    url = config.get(DOMAIN, {}).get(CONF_URL, DEFAULT_URL).rstrip("/")
    hass.http.register_view(StreamsView(url))
    hass.http.register_view(WebSocketView(url))
    return True


class StreamsView(HomeAssistantView):
    """GET /api/streams: la card lo usa para detectar el audio bidireccional."""

    url = f"{BASE_PATH}/streams"
    name = f"api:{DOMAIN}:streams"
    requires_auth = True

    def __init__(self, go2rtc: str) -> None:
        self._go2rtc = go2rtc

    async def get(self, request: web.Request) -> web.Response:
        session = async_get_clientsession(request.app["hass"])
        async with session.get(
            f"{self._go2rtc}/api/streams",
            params=_query(request),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            return web.Response(
                body=await resp.read(),
                status=resp.status,
                content_type=resp.content_type,
            )


class WebSocketView(HomeAssistantView):
    """GET /api/ws: señalización WebRTC/MSE, incluido el canal de vuelta."""

    url = f"{BASE_PATH}/ws"
    name = f"api:{DOMAIN}:ws"
    requires_auth = True

    def __init__(self, go2rtc: str) -> None:
        self._go2rtc = "ws" + go2rtc.removeprefix("http")

    async def get(self, request: web.Request) -> web.WebSocketResponse:
        server = web.WebSocketResponse(autoclose=False, autoping=False)
        await server.prepare(request)
        session = async_get_clientsession(request.app["hass"])
        try:
            async with session.ws_connect(
                f"{self._go2rtc}/api/ws",
                params=_query(request),
                autoclose=False,
                autoping=False,
            ) as client:
                await asyncio.wait(
                    [
                        asyncio.create_task(_forward(server, client)),
                        asyncio.create_task(_forward(client, server)),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )
        except aiohttp.ClientError as err:
            _LOGGER.warning("go2rtc no disponible: %s", err)
            await server.send_json({"type": "error", "value": str(err)})
        finally:
            await server.close()
        return server


async def _forward(src, dst) -> None:
    async for msg in src:
        if msg.type == aiohttp.WSMsgType.TEXT:
            await dst.send_str(msg.data)
        elif msg.type == aiohttp.WSMsgType.BINARY:
            await dst.send_bytes(msg.data)
        elif msg.type == aiohttp.WSMsgType.PING:
            await dst.ping(msg.data)
        elif msg.type == aiohttp.WSMsgType.PONG:
            await dst.pong(msg.data)
        else:
            break
