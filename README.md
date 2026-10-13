# Anyka — cámaras YI IoT en Home Assistant sin nube

Control local completo de cámaras YI IoT con SoC Anyka AK3918: vídeo RTSP, audio
bidireccional (micro y altavoz), movimiento, LEDs y filtro IR, todo desde Home
Assistant y sin la nube de YI. No se flashea nada: vive en la tarjeta SD.

Probado de punta a punta el 2026-10-13 en una YI IoT con AK3918 + GC1084 + Wi-Fi
ssv6x5x y Home Assistant 2026.9.

## Cómo funciona

```
Navegador (HA, HTTPS) ──WebRTC──▶ go2rtc (WebRTC Camera) ──RTSP :554──▶ libre_anyka_app ─ vídeo + micro
        micrófono ────────────────▶ go2rtc ─ffmpeg A-law─▶ TCP :10000 ─▶ ak_adec_demo ─ altavoz
Botones HA ─ shell_command ─ HTTP :8080/cgi-bin/ctl ─▶ PTZ (ptz_daemon), LEDs, filtro IR
```

| Carpeta | Qué hay |
|---|---|
| [`camera/`](camera/README.md) | Paquete de la SD: arranque desde `Factory/config.sh`, servicios vigilados, API de control, instalación por FTP y vuelta atrás |
| [`homeassistant/`](homeassistant/README.md) | Streams de go2rtc con canal de vuelta, `shell_command` de control y el panel |

## Puesta en marcha

1. Cámara: `camera/fetch-payload.sh` y `camera/install.sh <ip>`, y reiniciarla.
2. Home Assistant: seguir [`homeassistant/README.md`](homeassistant/README.md).
3. Abrir el panel por HTTPS para poder usar el micrófono.

## Lo que se descartó

El add-on Flask `anyka_audio`, la integración `anyka_talk`, la app de AppDaemon y el
overlay `camera_sd_overlay` se han eliminado: hablaban con un receptor que el firmware
YI no trae y no daban vídeo ni control. Tampoco funcionan en esta cámara `rtsp=1`/`onvif=1`
del firmware, el `v4l2rtspserver` del hack del Teckin TC100 ni `anyka-talkd`. Detalles en
[`camera/README.md`](camera/README.md).

⚠️ RTSP, foto, habla y el FTP del firmware no tienen contraseña: la cámara no debe ser
accesible desde Internet.
