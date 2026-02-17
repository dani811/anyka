# Anyka Camera SD Overlay (TCP Talk 10000)

Este paquete añade un **hook persistente de arranque** para cámaras Anyka mediante SD overlay.

## Qué instala

- `/etc/init.d/S95anyka_talk`: script de inicio que intenta arrancar el servicio de talk en el puerto `10000`.

## Instalación

1. Copia `camera_sd_overlay/` a la tarjeta SD de la cámara.
2. En la cámara, ejecuta:

```sh
sh /path/to/camera_sd_overlay/install.sh /
```

> Si tu firmware monta el overlay en otra ruta, pasa esa ruta como parámetro.

## Notas

- Puerto por defecto: `10000` (puedes cambiarlo con `ANYKA_TALK_PORT`).
- El script intenta usar binarios de talk comunes (`ai_talk`, `talk`).
- Si no encuentra binario compatible, deja trazas en `/tmp/anyka_talk_overlay.log`.
