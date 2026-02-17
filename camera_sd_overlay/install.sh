#!/bin/sh
set -eu

OVERLAY_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/overlay"
TARGET_ROOT="${1:-/}"

mkdir -p "${TARGET_ROOT}/etc/init.d"
cp "${OVERLAY_DIR}/etc/init.d/S95anyka_talk" "${TARGET_ROOT}/etc/init.d/S95anyka_talk"
chmod 0755 "${TARGET_ROOT}/etc/init.d/S95anyka_talk"

echo "Installed: ${TARGET_ROOT}/etc/init.d/S95anyka_talk"
