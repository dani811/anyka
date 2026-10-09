#!/usr/bin/env bash
set -euo pipefail

# Build anyka-talkd with the same AK3918 cross-toolchain/libraries used by
# ThatUsernameAlreadyExist/anyka-v4l2rtspserver.
#
# Prerequisites:
#   ANYKA_SOFTWARE_DIR - checkout of ThatUsernameAlreadyExist/anyka-software
#                       with ./crosscompiler.sh already completed.
#   ANYKA_RTSP_DIR     - checkout of ThatUsernameAlreadyExist/anyka-v4l2rtspserver

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANYKA_SOFTWARE_DIR="${ANYKA_SOFTWARE_DIR:?set ANYKA_SOFTWARE_DIR}"
ANYKA_RTSP_DIR="${ANYKA_RTSP_DIR:?set ANYKA_RTSP_DIR}"

HOST=arm-anykav200-linux-uclibcgnueabi
CC="${ANYKA_SOFTWARE_DIR}/arm-anykav200-crosstool/usr/bin/${HOST}-gcc"
INCLUDE_DIR="${ANYKA_RTSP_DIR}/libv4l2cpp/inc"
LIB_DIR="${ANYKA_RTSP_DIR}/libs"
OUT="${SCRIPT_DIR}/anyka-talkd"

test -x "$CC"
test -f "${INCLUDE_DIR}/ak_adec.h"
test -f "${LIB_DIR}/libmpi_adec.so"

"$CC" \
  -muclibc -std=gnu99 -O2 -Wall -Wextra -Werror \
  -I"$INCLUDE_DIR" \
  "$SCRIPT_DIR/anyka_talkd.c" \
  -L"$LIB_DIR" \
  -Wl,-rpath,/mnt/lib \
  -Wl,--no-as-needed \
  -lmpi_adec -lplat_ao -lplat_common -lplat_ipcsrv \
  -lakaudiocodec -lakaudiofilter -lak_mt -lplat_thread \
  -lrt -lpthread -ldl \
  -o "$OUT"

"${ANYKA_SOFTWARE_DIR}/arm-anykav200-crosstool/usr/bin/${HOST}-strip" "$OUT"

echo "Built: $OUT"
file "$OUT" || true

# Publish ABI/dependency evidence alongside the binary; no target execution.
READELF="${ANYKA_SOFTWARE_DIR}/arm-anykav200-crosstool/usr/bin/${HOST}-readelf"
{
  printf 'source_commit='
  git -C "$SCRIPT_DIR" rev-parse HEAD
  printf 'toolchain_commit='
  git -C "$ANYKA_SOFTWARE_DIR" rev-parse HEAD
  printf 'sdk_commit='
  git -C "$ANYKA_RTSP_DIR" rev-parse HEAD
  sha256sum "$OUT"
  "$READELF" -h -l -d "$OUT"
} > "$SCRIPT_DIR/build-info.txt"
