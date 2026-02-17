# anyka

Monorepo HAOS mínimo con un add-on para audio bidireccional inmediato en cámaras Anyka.

## Estructura

- `/repository.yaml`: índice del repositorio de add-ons para Home Assistant.
- `/addons/anyka-audio`: add-on HAOS que arranca go2rtc.

## Objetivo operativo

- **Downlink (escuchar):** stream RTSP expuesto por el add-on en `rtsp://<ha-ip>:8554/anyka`.
- **Uplink (hablar):** ruta de talkback configurada con `camera_talkback_url` (o `camera_rtsp_url` por defecto).

## Uso rápido

1. Añade este repositorio como repositorio de add-ons en Home Assistant.
2. Instala `Anyka Audio Bridge`.
3. Configura:
   - `camera_rtsp_url`
   - `camera_talkback_url` (opcional)
4. Inicia el add-on y valida:
   - API go2rtc: `http://<ha-ip>:1984`
   - RTSP local: `rtsp://<ha-ip>:8554/anyka`
   - Puerto adicional `tcp://<ha-ip>:10000` (canal auxiliar para integración de audio/talkback según despliegue)
