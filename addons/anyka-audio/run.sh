#!/usr/bin/env sh
set -eu

OPTIONS_FILE="/data/options.json"

if [ ! -f "$OPTIONS_FILE" ]; then
  echo "Missing $OPTIONS_FILE"
  exit 1
fi

CAMERA_RTSP_URL="$(jq -r '.camera_rtsp_url // empty' "$OPTIONS_FILE")"
CAMERA_TALKBACK_URL="$(jq -r '.camera_talkback_url // empty' "$OPTIONS_FILE")"

if [ -z "$CAMERA_RTSP_URL" ]; then
  echo "camera_rtsp_url is required"
  exit 1
fi

if [ -z "$CAMERA_TALKBACK_URL" ]; then
  CAMERA_TALKBACK_URL="$CAMERA_RTSP_URL"
fi

sed \
  -e "s|__CAMERA_RTSP_URL__|$CAMERA_RTSP_URL|g" \
  -e "s|__CAMERA_TALKBACK_URL__|$CAMERA_TALKBACK_URL|g" \
  /etc/go2rtc.yaml.template > /etc/go2rtc.yaml

exec /usr/local/bin/go2rtc -config /etc/go2rtc.yaml
