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

### Cámara montada de lado

Si la imagen sale girada, go2rtc la gira transcodificando en el host de HA (la cámara no
puede): cambia la primera fuente del stream por

```yaml
    - ffmpeg:rtsp://IP_CAMARA:554/vs0#video=h264#rotate=-90#audio=copy
```

(`-90` = 90° a la izquierda, `90` a la derecha, `180`). El canal de vuelta no cambia. Si
además usas una entidad Generic Camera, apúntala a `rtsp://127.0.0.1:8554/<stream>` para
que también salga girada.

## 2. Control (`configuration.yaml`)

```yaml
shell_command:
  yi_camara: "curl -s -m 5 http://IP_CAMARA:8080/cgi-bin/ctl?{{ query }}"
```

Se llama con `shell_command.yi_camara` y `data: {query: "cmd=ptz&arg=up"}`; órdenes en
`camera/README.md`. La API solo acepta la IP puesta en `CTL_ALLOW_IP` de la cámara.

## 3. Panel

`dashboard.yaml`: tarjeta `custom:webrtc-camera` con `media: video,audio,microphone`
y botones de PTZ, LEDs y filtro IR. Lo natural es añadir esa sección a la vista de
cámaras que ya tengas (en esta casa: Control → Cámaras), no crear un panel aparte. El micrófono del navegador solo funciona si HA se
abre por HTTPS.
