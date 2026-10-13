#!/bin/sh
# Compila libre_anyka_app desde el código de Gerge con nuestros parches, dentro de Docker.
# Resultado: camera/build/app/libre_anyka_app (lo recoge fetch-payload.sh).
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/source.lock"
BUILD="$HERE/../build/app"
SRC="$BUILD/src"
mkdir -p "$BUILD"

if [ ! -f "$BUILD/anyka_uclibc_gcc.tar.bz2" ]; then
	curl -fsSL -o "$BUILD/anyka_uclibc_gcc.tar.bz2" "$TOOLCHAIN_URL"
fi
echo "$TOOLCHAIN_SHA256  $BUILD/anyka_uclibc_gcc.tar.bz2" | shasum -a 256 -c -

if [ ! -d "$SRC/.git" ]; then
	git clone -q --filter=blob:none --sparse "$APP_REPO" "$SRC"
	git -C "$SRC" sparse-checkout set cross-compile/libre_anyka_app
fi
git -C "$SRC" fetch -q origin "$APP_COMMIT"
git -C "$SRC" checkout -q -f "$APP_COMMIT"
for p in "$HERE"/patches/*.patch; do
	git -C "$SRC" apply "$p"
done

cp "$HERE/Dockerfile" "$BUILD/Dockerfile"
docker build -q --platform linux/amd64 -t anyka-toolchain "$BUILD" >/dev/null
docker run --rm --platform linux/amd64 -v "$SRC/cross-compile/libre_anyka_app:/src" anyka-toolchain \
	arm-anykav200-linux-uclibcgnueabi-gcc main.c -std=c99 -D_POSIX_C_SOURCE=199309L -Iinclude -Llib \
	-lakuio -lakispsdk -lakv_encode -lplat_common -lplat_thread -lplat_vi -lplat_vpss -lplat_ipcsrv \
	-lplat_venc_cb -lmpi_venc -lakstreamenc -lpthread -lakae -lakaudiocodec -lakmedia -lakv_encode \
	-lapp_net -lapp_rtsp -lmpi_aed -lmpi_aenc -lplat_ai -lplat_drv -o libre_anyka_app
cp "$SRC/cross-compile/libre_anyka_app/libre_anyka_app" "$BUILD/libre_anyka_app"
echo "Compilado: $BUILD/libre_anyka_app"
