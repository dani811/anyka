# Arquitectura: cámaras YI IoT con audio bidireccional mediante go2rtc

Estado: arquitectura acordada; adaptador AK3918 experimental. Ninguna cámara YI
IoT del usuario tiene todavía una validación física documentada para este daemon.
La marca de la app no identifica el SoC, ABI, sensor ni SDK de una cámara.

## Objetivo y límites

Integrar vídeo, escucha y pulsar-para-hablar (PTT) en Home Assistant a través de
go2rtc, conservando el stream funcional de cada cámara. El primer criterio de
aceptación es PTT fiable. Dúplex simultáneo, cancelación de eco, PTZ y persistencia
son capacidades independientes que requieren sus propias pruebas.

```text
Cámara: vídeo + micrófono --RTSP--> go2rtc --WebRTC--> navegador / tarjeta HA
Cámara: altavoz <--ak_ao-- ak_adec <--PCMA/TCP-- ffmpeg <--PCMA-- go2rtc <--WebRTC-- micrófono
                         anyka-talkd          exec backchannel
```

## Responsabilidades

| Componente | Responsabilidad | No debe asumir |
|---|---|---|
| Navegador/tarjeta | Permiso de micrófono, HTTPS, PTT, reproducción | Acceso TCP directo a la cámara |
| go2rtc | Sesiones WebRTC, negociación de codecs, RTSP existente | Que todas las cámaras tengan backchannel |
| ffmpeg iniciado por exec | Extraer/enviar PCMA crudo a TCP, sin recodificar | Que TCP abierto implique audio físico |
| anyka-talkd | Un emisor autorizado, límites de sesión, SDK de audio | ONVIF, UI, Flask, descubrimiento, credenciales HA |
| Firmware/SDK | Decoder, driver, DAC y control físico del altavoz | Compatibilidad entre variantes por marca comercial |
| Home Assistant | Entidades, acceso del usuario y presentación | Mantener una segunda pila de audio por chunks |

La cámara que ya tenga un backchannel nativo compatible con go2rtc utiliza ese
camino. Solo las cámaras sin él necesitan el adaptador. Nunca instalar el daemon
por el mero hecho de usar YI IoT o por aparecer como ONVIF.

## Contrato del adaptador AK3918

- IPv4/TCP; puerto configurable (10000 por defecto); `--allow` obligatorio.
- Payload: G.711 A-law (PCMA), 8000 muestras/s, mono, 1 byte/muestra (8000 B/s).
- Sin cabecera WAV, RTP, HTTP, autenticación propia ni cifrado.
- Fragmentación TCP arbitraria: no se interpretan límites de paquetes como frames.
- SDK: `ak_adec` decodifica a PCM de 16 bits; `ak_ao` entrega al altavoz.
- El primer byte de audio adquiere el dispositivo; conectar no abre el altavoz.
- Un cliente activo; conexiones adicionales se cierran, no se encolan como PTT.
- 3 s sin datos, 120 s de sesión total o 1 s sin avance del decoder terminan sesión.
- EOF y SIGTERM liberan recursos. El cliente debe reconectar después del timeout.
- Volumen inicial DAC 2/6. El volumen adecuado y ASLC necesitan validación física.
- Los límites controlan nuestro bucle; no pueden garantizar que una biblioteca
  propietaria bloqueada en `ak_adec_cancel_stream` retorne. Registrar duración de
  cierre real antes de activar persistencia. No matar/reiniciar procesos del firmware.

## Despliegue y red

`exec` y ffmpeg se ejecutan **dentro del mismo entorno que go2rtc**, no en el
navegador, ni necesariamente en Home Assistant Core. `--allow` debe coincidir con
la IP de origen que realmente ve la cámara (teniendo en cuenta NAT/contenedores).
La allowlist es filtrado de red, no autenticación criptográfica. Mantener el
servicio en una red de confianza; no abrir puertos de Internet.

Usar rutas fijas configuradas por el administrador; no interpolar texto recibido
del navegador en comandos exec. Si go2rtc usa `exec.allow_paths`, autorizar solo la
ruta real de ffmpeg. Mantener las credenciales RTSP fuera de GitHub y los informes.

Cada cámara tiene un identificador de stream estable y un destino TCP propio.
No hay registro global ni sesión compartida de cámara en el adaptador. La
exclusión física se aplica por daemon. Comprobar NAT antes de elegir la allowlist.

## Decisiones y migración

1. **go2rtc es la capa multimedia común.** Reutilizar su WebRTC y codec PCMA en vez
   de ampliar el transporte Flask/MediaRecorder del add-on 2.x.
2. **Adaptador por capacidad/ABI, no por marca.** AK3918 es el primer candidato;
   otros SoC necesitan evidencia y, si procede, un adaptador distinto.
3. **Pruebas progresivas.** Compilar, verificar ABI, probar silencio y cierre,
   micrófono PTT, escucha simultánea, recuperación y solo después arranque.
4. **Migración reversible.** Mantener `develop` y la ruta antigua hasta superar
   aceptación física. PR #15 se reevalúa después; no trasladar automáticamente su
   gestión de sesiones a go2rtc.
5. **GitHub conserva contratos y evidencia reproducible.** Informes locales de
   dispositivos y credenciales no se versionan; solo resultados saneados.

## Fuentes y evidencia

- go2rtc v1.9.14, commit `b5948cfb25404cc5cb37b166ecaa2dca20b11d4b`:
  [exec](https://github.com/AlexxIT/go2rtc/blob/b5948cfb25404cc5cb37b166ecaa2dca20b11d4b/internal/exec/exec.go),
  [PCMA backchannel](https://github.com/AlexxIT/go2rtc/blob/b5948cfb25404cc5cb37b166ecaa2dca20b11d4b/pkg/pcm/backchannel.go).
- [Compatibilidad y estado de las pruebas](COMPATIBILITY.md).
- [Procedimiento y criterios de aceptación](VALIDATION.md).
