# Home Assistant — cámara YI (paquete `camera/`)

Probado el 2026-10-13 con HA 2026.9 y la integración **WebRTC Camera** (AlexxIT), que
arranca su propio go2rtc en `:1984` y lee `/config/go2rtc.yaml`. El go2rtc integrado en
HA no admite streams `exec`, así que el habla necesita ese go2rtc (o la app go2rtc).

## 1. go2rtc (`/config/go2rtc.yaml`)

```yaml
streams:
  yi_camara:
    - rtsp://IP_CAMARA:554/vs0
    - exec:ffmpeg -hide_banner -loglevel error -f alaw -ar 8000 -ac 1 -i - -c:a copy -f alaw tcp://IP_CAMARA:10000#backchannel=1#audio=alaw/8000
  yi_camara_sub:
    - rtsp://IP_CAMARA:554/vs1
```

La segunda línea es el canal de vuelta: go2rtc pasa el micrófono del navegador
(PCMA 8 kHz) a ffmpeg, que lo manda al receptor de la cámara en `:10000`. Tras editar,
recarga la integración WebRTC Camera.

## 2. Control (`configuration.yaml`)

```yaml
shell_command:
  yi_camara: "curl -s -m 5 http://IP_CAMARA:8080/cgi-bin/ctl?{{ query }}"
```

Se llama con `shell_command.yi_camara` y `data: {query: "cmd=ptz&arg=up"}`; órdenes en
`camera/README.md`. La API solo acepta la IP puesta en `CTL_ALLOW_IP` de la cámara.

## 3. Panel

`dashboard.yaml`: tarjeta `custom:webrtc-camera` con `media: video,audio,microphone`
y botones de PTZ, LEDs y filtro IR. El micrófono del navegador solo funciona si HA se
abre por HTTPS.
