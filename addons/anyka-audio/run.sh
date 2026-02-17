#!/usr/bin/env sh
set -eu

options_file="/data/options.json"

if [ ! -f "$options_file" ]; then
  echo "Missing $options_file"
  exit 1
fi

camera_rtsp_url="$(jq -r '.camera_rtsp_url // empty' "$options_file")"
camera_talkback_url="$(jq -r '.camera_talkback_url // empty' "$options_file")"

if [ -z "$camera_rtsp_url" ]; then
  echo "camera_rtsp_url is required"
  exit 1
fi

if [ -z "$camera_talkback_url" ]; then
  camera_talkback_url="$camera_rtsp_url"
fi

sed \
  -e "s|__CAMERA_RTSP_URL__|$camera_rtsp_url|g" \
  -e "s|__CAMERA_TALKBACK_URL__|$camera_talkback_url|g" \
  /etc/go2rtc.yaml.template > /etc/go2rtc.yaml

exec /usr/local/bin/go2rtc -config /etc/go2rtc.yaml
