# PoC: simplify Anyka two-way audio around go2rtc

Tracks #16.

## Target architecture

Do not implement ONVIF, WebRTC, microphone capture, session management or
transcoding in the Home Assistant add-on.

Use the standard path whenever the camera supports it:

```text
browser / Advanced Camera Card
             |
           WebRTC
             |
           go2rtc
             |
      RTSP/ONVIF backchannel
             |
           camera
```

Legacy Anyka cameras such as the tested Teckin TC100 do not currently expose a
usable RTSP/ONVIF backchannel. For them the only Anyka-specific component is a
small camera-side sink:

```text
browser
  |
WebRTC
  |
go2rtc
  |
PCMA/8000 backchannel
  |
exec + ffmpeg codec-copy
  |
TCP/10000
  |
anyka-talkd
  |
ak_adec (G.711 A-law)
  |
ak_ao
  |
speaker
```

## What was validated on the real TC100

The PoC was tested against the existing Home Assistant/go2rtc setup without
changing the production camera entity.

Verified:

- the existing TC100 downlink works through go2rtc via the current RTSP source;
- go2rtc accepts a second `exec` producer as a backchannel;
- that producer is exposed internally as **audio / sendonly / PCMA / 8000 Hz**;
- therefore the WebRTC -> go2rtc half already provides exactly the codec the
  AK3918 decoder accepts;
- the tested TC100 did **not** have TCP/10000 open, so assuming a pre-existing
  talk listener was incorrect;
- the hack's ONVIF service is configured as discovery/profile metadata around
  the existing RTSP streams; it does not configure a Profile-T audio
  backchannel;
- on the tested camera the hack's ONVIF port (8081) was not listening.

The temporary go2rtc change used for this test was rolled back after the probe.

## Why `anyka-talkd`

The Anyka SDK already provides everything needed for the last hop:

- `AK_AUDIO_TYPE_PCM_ALAW`;
- `ak_adec_open()` / `ak_adec_send_stream()`;
- `ak_adec_request_stream()`;
- `ak_ao_open()` and speaker controls.

So `camera_talkd/anyka_talkd.c` intentionally does only this:

1. listen on a TCP port (default 10000);
2. accept one talk session;
3. decode raw PCMA/G.711 A-law at 8 kHz mono;
4. feed it to the AK3918 audio output;
5. tear the decoder/output down on disconnect.

There is no HTTP API, Flask, CORS, camera registry, MediaRecorder endpoint,
RTSP parser or ONVIF implementation in this daemon.

## go2rtc configuration after the daemon is installed

See [go2rtc.yaml.example](go2rtc.yaml.example).

```yaml
streams:
  anyka_poc:
    - "rtsp://CAMERA_IP:554/YOUR_WORKING_RTSP_PATH#backchannel=0"
    - "exec:ffmpeg -hide_banner -loglevel error -f alaw -ar 8000 -ac 1 -i pipe:0 -map 0:a:0 -c:a copy -f alaw tcp://CAMERA_IP:10000#backchannel=1#audio=alaw/8000"
```

The second source contains no transcoding: go2rtc already supplies PCMA/8000,
so ffmpeg is used only as the guaranteed-available pipe-to-TCP transport.

## Security

The old Home Assistant bridge exposed a much larger control surface. This
design removes the need for:

- custom Flask/Ingress talk API;
- global CORS;
- client-provided camera IP/port/RTSP targets;
- custom browser microphone/chunk handling;
- Home Assistant-side FFmpeg process/session state.

The legacy camera listener is still a raw audio service. It must remain on the
trusted LAN. `anyka-talkd` supports `--allow IPv4` so deployments can accept
audio only from the Home Assistant/go2rtc host.

## Atomic rollout

1. Cross-compile `anyka-talkd` for AK3918 in CI.
2. Verify the produced binary architecture and dynamic dependencies.
3. Copy only that binary to the TC100 SD overlay.
4. Start it manually first; confirm TCP/10000 is listening.
5. Send a short **silence** PCMA stream and verify the daemon stays healthy.
6. Add the go2rtc backchannel source and verify it reports
   `audio sendonly PCMA/8000`.
7. Test microphone audio from the existing WebRTC card.
8. Test repeated PTT start/stop.
9. Only after those checks, make the camera daemon persistent at boot.
10. Deprecate the old Flask uplink in a separate PR.

## Native ONVIF/Profile-T cameras

They should bypass this compatibility layer entirely. If go2rtc discovers a
working RTSP audio backchannel, use that directly.

The purpose of this repository should therefore become **legacy Anyka
compatibility**, not a second generic camera/media stack.
