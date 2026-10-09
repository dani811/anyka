# anyka-talkd

Minimal PCMA talk sink for Anyka AK3918 cameras.

## Contract

Input is deliberately fixed:

- TCP;
- raw G.711 A-law / PCMA;
- 8000 Hz;
- mono;
- one active client at a time.

The daemon decodes through the Anyka SDK and writes to the physical speaker via
`ak_ao`.

## Build

Use the same cross-toolchain and vendor libraries as
`ThatUsernameAlreadyExist/anyka-v4l2rtspserver`.

```bash
git clone https://github.com/ThatUsernameAlreadyExist/anyka-software.git
git clone https://github.com/ThatUsernameAlreadyExist/anyka-v4l2rtspserver.git

cd anyka-software
./crosscompiler.sh
cd ..

ANYKA_SOFTWARE_DIR="$PWD/anyka-software" \
ANYKA_RTSP_DIR="$PWD/anyka-v4l2rtspserver" \
./camera_talkd/build.sh
```

CI performs the same cross-build.

## Run

```sh
LD_LIBRARY_PATH=/mnt/lib:/lib:/usr/lib \
  /mnt/bin/anyka-talkd --port 10000 --allow VERIFIED_GO2RTC_SOURCE_IP
```

For first hardware validation, run it manually. Do not enable autostart until a
silence stream and repeated connect/disconnect cycles have passed.

## Design limits

This is intentionally not an RTSP or ONVIF server. Native Profile-T cameras
already have that protocol and should connect to go2rtc directly.

For legacy Anyka, go2rtc provides the standard WebRTC-facing backchannel and
this daemon is only the hardware compatibility endpoint.

## Session policy and evidence

`--allow` is mandatory. Default DAC volume is 2/6. The speaker opens on the first
audio bytes, never on a TCP probe. An idle client is closed after 3 seconds;
a session lasts at most 120 seconds. A stalled decoder is abandoned after 1 second
without progress. Additional clients are rejected while one owns the session.

SDK cancellation may itself block; hardware close latency is an explicit test gate.
Host tests use a fake SDK and cannot prove hardware compatibility.

See [architecture](../docs/ARCHITECTURE.md), [compatibility](../docs/COMPATIBILITY.md)
and [validation](../docs/VALIDATION.md). The old SD overlay is not an installer for
this daemon. Use manual, temporary deployment only after checking the target ABI.
