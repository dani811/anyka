# Validación progresiva y recuperación

No habilitar autostart ni sustituir firmware antes de superar las pruebas manuales.
Una compilación correcta o una conexión TCP no equivalen a audio bidireccional.

## 1. Pruebas de host (sin cámara)

```sh
python3 -m unittest discover -s tests -v
python3 tests/check_go2rtc_transport.py /ruta/a/go2rtc
```

La primera compila el daemon real con un SDK falso y prueba sesiones TCP,
fragmentación/escrituras parciales, allowlist, cliente ocupado, timeout, fallos de
inicialización y SIGTERM. No valida el SDK propietario.

La segunda usa go2rtc y ffmpeg reales en loopback, genera silencio A-law y
comprueba 16000 bytes `0xD5` recibidos (2 s de muestras PCMA/8000). Sus puertos son
locales y temporales. No accede a cámaras, no abre micrófonos y no modifica HA.
No prueba el tramo WebRTC del navegador ni el altavoz.

## 2. Identificar y comprobar el binario

Desde una shell ya autorizada en la cámara, ejecutar el contenido de
`scripts/camera_inventory.sh`; guardar la salida **fuera de Git**. Comparar la ABI,
intérprete ELF y dependencias del artefacto ARM con las bibliotecas del firmware.
El pipeline publica `build-info.txt` con las dependencias y hashes. No copiar
bibliotecas de otra cámara para solventar incompatibilidades a ciegas.

Confirmar IP y dispositivo con el usuario. Las IP de carpetas antiguas no son un
inventario actual. Identificar el punto de montaje SD y una ruta temporal libre.
No reutilizar el hook antiguo `S95anyka_talk`: supone incorrectamente que programas
como `ak_adec_demo` aceptan un puerto TCP; su presencia no demuestra un servidor.

## 3. Inicio manual y silencio

Guardar los hashes del binario y configuración actuales. Copiar solo el artefacto
compatible a una ruta temporal/SD nueva; no tocar flash ni scripts de arranque.
Desde la shell de la cámara (sustituir rutas y origen por valores verificados):

```sh
LD_LIBRARY_PATH=/RUTA/LIBS_VERIFICADAS /RUTA/anyka-talkd \
  --port 10000 --allow IP_ORIGEN_GO2RTC --volume 2
```

Mantener el proceso en primer plano para detenerlo con Ctrl-C. Confirmar que un
origen distinto se rechaza y que una conexión sin audio no adquiere el altavoz.
Desde el host autorizado enviar silencio durante 2 s:

```sh
ffmpeg -hide_banner -loglevel error -re -f lavfi \
  -i anullsrc=r=8000:cl=mono -t 2 -c:a pcm_alaw -f alaw tcp://IP_CAMARA:10000
```

Revisar errores, tiempo de cierre, memoria/procesos y que RTSP sigue funcionando.
Si hay bloqueo del SDK, parar la prueba; no reiniciar automáticamente la cámara.
El silencio prueba estabilidad, no reproducción audible.

## 4. go2rtc y PTT

1. Guardar copia de la configuración go2rtc y versión instalada.
2. Crear un stream de prueba con nombre nuevo, conservando el RTSP existente.
3. Aplicar el ejemplo de `poc/go2rtc-anyka/go2rtc.yaml.example` solo en la instancia
   elegida. Comprobar ffmpeg, soporte exec y la IP de origen desde su contenedor.
4. Confirmar PCMA/8000 sendonly. Esto es negociación, no prueba audible.
5. En HTTPS abrir una tarjeta compatible con micrófono WebRTC. El usuario concede
   el permiso y pronuncia una frase breve; otra persona confirma el altavoz.
6. Repetir 20 ciclos PTT inicio/parada; registrar pérdidas, cierres y latencia.
7. Probar escucha RTSP mientras se habla. Registrar eco y contención; no afirmar
   dúplex completo o cancelación de eco sin comprobarlo.
8. Probar cierre de pestaña, pérdida de red e inactividad. Volver a conectar tras
   3 s sin datos y tras el máximo de 120 s. Confirmar que RTSP no se interrumpe.

Registrar: perfil de cámara, SHA, bibliotecas, go2rtc/ffmpeg, origen, fecha,
resultado esperado/observado, logs saneados y confirmación humana de audio. No
publicar audio de personas, direcciones ni credenciales.

## 5. Reversión y promoción

- Detener solo el PID iniciado por esta prueba; no usar `killall` del firmware.
- Retirar el stream de prueba/restaurar su configuración previa.
- Retirar únicamente el binario temporal que se copió y verificar RTSP previo.
- Si todas las pruebas pasan, diseñar en otro cambio la persistencia específica
  del firmware, con PID, parada, rollback y configuración por cámara.
- Retirar Flask/Ingress solo después de migración validada, nunca solo por CI verde.
