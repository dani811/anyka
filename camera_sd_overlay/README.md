# Anyka Camera SD Overlay (TCP Talk 10000)

This package adds a **persistent boot hook** for Anyka cameras using an SD overlay.

## What it installs

- `/etc/init.d/S95anyka_talk`: startup script that attempts to start talk service on port `10000`.

## Installation

1. Copy `camera_sd_overlay/` to the camera SD card.
2. On the camera, run:

```sh
sh /path/to/camera_sd_overlay/install.sh /
```

> If your firmware mounts overlay files under a different root path, pass that path as the parameter.

## Notes

- Default port: `10000` (override with `ANYKA_TALK_PORT`).
- The script tries common talk binaries (`ai_talk`, `talk`).
- If no compatible binary is found, logs are written to `/tmp/anyka_talk_overlay.log`.
