# PoC: native go2rtc backchannel for Anyka

Tracks #16.

## Objective

Validate that the custom Anyka Flask/Ingress uplink can be replaced by a native
go2rtc backchannel.

The camera already accepts talk audio as raw **PCMA / G.711 A-law, 8000 Hz,
mono** on a TCP socket (normally port `10000`). Current go2rtc supports an
`exec` source with `backchannel=1` and can write **PCMA** directly to the
child process stdin.

That gives us a much smaller path:

```text
Browser microphone
      |
    WebRTC
      |
    go2rtc
      |
 PCMA/alaw 8 kHz
      |
 exec stdin
      |
    ffmpeg       (codec copy only)
      |
 TCP :10000
      |
 Anyka speaker
```

The RTSP source remains responsible only for camera -> browser video/audio.

## Why ffmpeg is used in this PoC

go2rtc's current Docker image explicitly includes `ffmpeg`. The PoC therefore
does not depend on `nc`, `socat`, Python, Flask, or another runtime being
present.

The command intentionally uses `-c:a copy`: go2rtc already provides
`alaw/8000`, so ffmpeg should only demux the raw A-law input and mux the same
bytes to the TCP URL. No audio transcoding is expected.

## Configuration

Start from [go2rtc.yaml.example](go2rtc.yaml.example):

```yaml
streams:
  anyka_poc:
    - "rtsp://CAMERA_IP:554/YOUR_WORKING_RTSP_PATH#backchannel=0"
    - "exec:ffmpeg -hide_banner -loglevel error -f alaw -ar 8000 -ac 1 -i pipe:0 -map 0:a:0 -c:a copy -f alaw tcp://CAMERA_IP:10000#backchannel=1#audio=alaw/8000"
```

Important details:

- The RTSP line has `#backchannel=0` because this legacy Anyka path does not use
  an RTSP/ONVIF backchannel.
- The second source advertises a go2rtc backchannel with
  `#backchannel=1#audio=alaw/8000`.
- The destination IP and talk port are static configuration. They are **not**
  supplied by a browser/API request.
- Keep the complete source strings quoted in YAML because `#` is otherwise a
  YAML comment delimiter.

## Atomic validation procedure

Use one known-working Anyka camera.

### 1. Baseline

Before changing go2rtc:

- confirm the existing RTSP URL has video;
- confirm its camera audio works if the camera exposes audio;
- confirm TCP talk port `10000` is listening using the existing Anyka setup.

Do not continue if the current camera talk path is already broken.

### 2. Add only the PoC stream

Add `anyka_poc` to go2rtc without replacing the existing production stream.

Reload/restart only go2rtc as required by the environment.

### 3. Probe the stream

In the go2rtc WebUI, probe `anyka_poc`.

Expected:

- camera video/audio tracks come from the RTSP source;
- a backchannel audio track is available as PCMA/A-law 8000 Hz.

If the RTSP source itself advertises a broken backchannel, ensure
`#backchannel=0` remains present on that source.

### 4. Test browser -> camera audio

Open `anyka_poc` through the existing WebRTC/Advanced Camera Card path and
activate two-way audio.

Success means:

- the browser requests microphone permission;
- speaking into the browser is heard on the Anyka camera speaker;
- no request reaches the custom Flask `:8099` uplink API;
- stopping talk terminates the ffmpeg exec process.

### 5. Observe failure modes

Record which layer fails:

| Symptom | Likely layer |
| --- | --- |
| No video | RTSP source/path |
| No microphone control | WebRTC/card did not see backchannel |
| ffmpeg exits immediately | exec syntax/input format/TCP connection |
| ffmpeg stays alive but camera is silent | Anyka framing/codec assumption |
| Sound is distorted | sample format/rate/channel mismatch |
| Works once but not again | camera talk server lifecycle/session handling |

## Success criteria

The PoC passes only if all are true:

1. video/audio downlink continues to work through go2rtc;
2. browser microphone reaches the camera speaker;
3. audio is intelligible with acceptable latency;
4. repeated start/stop works;
5. the custom Anyka HTTP uplink is not involved.

## Failure interpretation

The most important unknown is **framing**.

go2rtc documents that an exec backchannel can provide PCMA directly on stdin.
Our existing bridge sends raw `-f alaw` to the Anyka TCP socket. If this PoC is
silent while the old bridge works, capture/compare the bytes on the two paths
before adding more architecture.

Do **not** immediately add another HTTP service. First determine whether Anyka
needs:

- pure raw A-law bytes;
- an initial proprietary header/handshake;
- fixed packet sizes/timing;
- a camera-side talk process to be started differently.

## Security properties of this design

Compared with the current custom Flask API, this PoC removes the need for:

- a public `:8099` control API;
- global Flask CORS;
- browser-supplied `camera_ip`;
- browser-supplied `audio_port`;
- browser-supplied `rtsp_url`;
- our own MediaRecorder chunk API;
- our own FFmpeg process/session manager.

The camera destination is an allowlisted/static go2rtc configuration entry.

The Anyka TCP talk service itself is still unauthenticated/legacy and should
remain reachable only from trusted local infrastructure.

## If the PoC passes

The next change should **not** be to expand the current Flask add-on.

Instead:

1. keep native ONVIF/RTSP backchannel cameras entirely in go2rtc;
2. keep this small exec adapter only for legacy Anyka;
3. deprecate the custom Flask uplink and HACS talk integration;
4. retain the SD overlay only where a camera needs it to keep the Anyka talk
   service alive;
5. remove the old stack in a separate migration PR after real-camera testing.

## Rollback

Remove the `anyka_poc` stream and restart/reload go2rtc. No existing Anyka
files or Home Assistant entities are modified by this PoC.
