# go2rtc + adaptador Anyka AK3918

Tracks #16. El objetivo son cámaras genéricas de la plataforma YI IoT. Su hardware
concreto debe identificarse antes de probar este daemon.

[Arquitectura](../../docs/ARCHITECTURE.md) ·
[Compatibilidad](../../docs/COMPATIBILITY.md) ·
[Validación y rollback](../../docs/VALIDATION.md)

## Camino de audio

```text
micrófono del navegador -> WebRTC -> go2rtc -> exec/ffmpeg -> PCMA TCP
-> anyka-talkd -> ak_adec -> ak_ao -> altavoz
```

Vídeo y escucha conservan el RTSP existente hacia go2rtc. Para cámaras con
backchannel nativo compatible se usa ese soporte directamente.

## Configuración

[go2rtc.yaml.example](go2rtc.yaml.example) muestra un stream nuevo con dos fuentes:
RTSP existente y exec de retorno. Sustituir los marcadores por valores verificados.
El proceso ffmpeg corre en el entorno de go2rtc; `--allow` en la cámara usa la IP
que ese entorno presenta a la red. No confundirla automáticamente con HA Core.

PCMA es G.711 A-law mono de 8 kHz. El comando de retorno copia el codec y elimina
cualquier contenedor; no implementa una segunda captura de micrófono.

## Estado

La compilación ARM se verificó en el commit 4911917. Las atribuciones anteriores de
pruebas con una TC100 fueron cuestionadas por el usuario y se han retirado como
base de compatibilidad. La prueba reproducible de host y su alcance se describen
en VALIDATION.md; el audio físico y el tramo de micrófono/WebRTC siguen pendientes.

No habilitar arranque automático ni retirar el add-on antiguo antes de completar
la validación en una cámara YI IoT identificada.
