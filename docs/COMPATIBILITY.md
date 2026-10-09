# Compatibilidad y evidencia

Actualizado: 2026-10-09. Este documento distingue código, pruebas de host y hardware.

| Elemento | Evidencia disponible | Lo que no demuestra |
|---|---|---|
| Objetivo YI IoT | Usuario confirma cámaras genéricas chinas con esa app | Modelo, SoC, ABI o servicio de audio |
| Copia local histórica | Configuración ISP GC1084; copia sin `/usr` | Sensor actual, identidad de una IP, backup restaurable completo |
| Firmware de referencia | Algunos scripts cargan GC1054; SDK Anyka incluido | Que deba instalarse ese firmware en las cámaras objetivo |
| CI ARM del PR #17, commit 4911917 | Compilación/enlace correctos, run 37906200889 | Ejecución ni audio físico |
| Pruebas de host | TCP, sesiones y errores mediante SDK simulado | Comportamiento del decoder/driver propietario |
| Transporte go2rtc | Ver `VALIDATION.md` y prueba loopback reproducible | Permiso de micrófono, WebRTC del navegador, altavoz |
| Teckin TC100 | Atribuciones antiguas del issue/PR cuestionadas por el usuario | Ninguna validación aceptada de las cámaras YI IoT |

Las afirmaciones anteriores de «probado en la TC100» no se usan como evidencia.
No se sustituye esa marca por YI IoT en resultados antiguos: la prueba física está
pendiente y debe repetirse sobre un dispositivo identificado.

## Perfil de una cámara candidata (completar antes de copiar ejecutables)

- Identificador local y confirmación humana de qué cámara es.
- App: YI IoT (no equivale a Xiaomi Mi Home).
- Modelo/placa/SoC: desconocidos hasta evidencia.
- CPU/arquitectura y endianness; intérprete ELF y versión libc.
- Kernel, módulos de audio, bibliotecas y símbolos SDK disponibles.
- Firmware y configuración ISP; no cambiar sensor para habilitar audio.
- RTSP funcional y codecs anunciados, sin publicar credenciales.
- Acceso autorizado actual: SSH/Telnet/SD, sin abrir nuevos servicios por defecto.
- Proceso que usa el altavoz y posible exclusión con el firmware.
- Backup y vía de recuperación antes de cualquier cambio persistente.

`scripts/camera_inventory.sh` recoge un subconjunto no sensible desde una shell
ya autorizada. No lee contraseñas Wi-Fi, shadow, claves ni imágenes. No detecta
por sí solo toda la compatibilidad: completar el perfil con evidencia manual.
