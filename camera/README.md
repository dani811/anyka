# Paquete de cámara (SD) — YI IoT AK3918

Control local de la cámara sin la nube de YI y sin flashear nada. Todo vive en la
tarjeta SD; si se saca, la cámara vuelve al firmware original.

## Hardware probado

| | |
|---|---|
| SoC | Anyka AK3918 (ARM926EJ-S), 36 MB RAM, kernel 3.4.35 |
| Sensor | GC1084 |
| Wi-Fi | ssv6x5x |
| Extras | 2 motores (`/dev/ak-motor0/1`), altavoz (`SPK_PA`), micro, LED IR, LED blanco, IR-cut |

## Cómo arranca

El firmware ejecuta `/mnt/Factory/config.sh` en lugar de `daemon` + `anyka_ipc` cuando
existe la carpeta `Factory` en la SD. Nuestro `config.sh` levanta la red original,
Telnet de emergencia y `/mnt/anyka/start.sh`, que vigila estos servicios:

| Servicio | Qué da | Binario |
|---|---|---|
| Vídeo + micro | `rtsp://IP:554/vs0` (1280x720 H.264 + A-law), `/vs1` (sub), `http://IP:3000/snapshot.jpeg` | `libre_anyka_app` |
| PTZ e IR-cut | FIFO `/tmp/ptz.daemon` | `ptz_daemon_dyn` |
| Habla | TCP `:10000`, G.711 A-law 8 kHz mono → altavoz | `ak_adec_demo` (firmware) |
| Control | `http://IP:8080/cgi-bin/ctl?cmd=…` | `busybox httpd` |

Lo que **no** sirve en esta cámara (comprobado 2026-10-13): `rtsp=1`/`onvif=1` en
`anyka_cfg.ini` (el `anyka_ipc` de YI no lleva servidor RTSP), el `v4l2rtspserver` del
hack del Teckin TC100 (falta `libakmedialib.so`) y `anyka-talkd` (faltan librerías).

## API de control

| Orden | Ejemplo |
|---|---|
| Mover | `ctl?cmd=ptz&arg=up` (`down`, `left`, `right`, `left_up`, …, `home`) |
| Ir a posición | `ctl?cmd=goto&pan=180&tilt=60` (tilt 0 = arriba) |
| Filtro IR | `ctl?cmd=ir_cut&arg=on` (puesto, color normal) / `off` (quitado, imagen magenta) |
| LED IR | `ctl?cmd=ir_led&arg=on` / `off` |
| LED blanco | `ctl?cmd=white_led&arg=on` / `off` |
| Estado | `ctl?cmd=status` |

El filtro IR se mueve escribiendo el pin `gpio-ircut_a` (1 = puesto); `set_ir_cut` del
`ptz_daemon` no lo mueve en esta placa. Con `VIDEO_ARGS="-i 4"` (inversión día/noche) la
imagen sale en gris a plena luz; esta cámara usa `-i 1`.

Solo acepta esas órdenes. Para limitarla a Home Assistant, pon su IP en
`CTL_ALLOW_IP` de `sd/anyka/anyka.conf`.

⚠️ El RTSP, la foto, la habla y el FTP del firmware no tienen contraseña: la cámara
no debe ser accesible desde Internet.

## Nuestro `libre_anyka_app`

Se compila desde el código de Gerge (`app/source.lock`) con los parches de `app/patches/`,
usando la toolchain de Anyka dentro de Docker (`app/build.sh`, Docker Desktop arrancado):

- El servidor de fotos (:3000) cierra y sigue cuando rechaza una petición; antes una
  conexión vacía (un escaneo de puertos) tumbaba el programa con SIGSEGV.
- `SO_REUSEADDR` en :3000: al relanzarse, el puerto ya no se queda sin abrir.
- SIGPIPE ignorado: un cliente que corta a mitad de envío no lo mata.
- Filtro IR con la polaridad de esta cámara: de día queda puesto (antes, imagen magenta).

## Instalar

```sh
camera/fetch-payload.sh          # compila libre_anyka_app y descarga el resto (payload.lock)
camera/install.sh 192.168.68.103 # copia de seguridad + subida por FTP
```

Reinicia la cámara. Para deshacer: `camera/rollback.sh <ip> camera/backups/<copia>`,
o saca la SD.

## Origen de los binarios

`ptz_daemon_dyn`, `busybox` y las librerías de `libre_anyka_app` vienen de
[jphein/anyka3918-gc1084-camera](https://github.com/jphein/anyka3918-gc1084-camera)
(GPLv3, basado en el trabajo de Gerge y kuhnchris). No se versionan aquí; se
descargan del commit fijado en `payload.lock`.
