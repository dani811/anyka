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
  /mnt/bin/anyka-talkd --port 10000 --allow HOME_ASSISTANT_LAN_IP
```

For first hardware validation, run it manually. Do not enable autostart until a
silence stream and repeated connect/disconnect cycles have passed.

## Design limits

This is intentionally not an RTSP or ONVIF server. Native Profile-T cameras
already have that protocol and should connect to go2rtc directly.

For legacy Anyka, go2rtc provides the standard WebRTC-facing backchannel and
this daemon is only the hardware compatibility endpoint.
