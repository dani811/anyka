#!/bin/sh
# Descarga los binarios ARM de terceros (GPLv3) desde un commit fijado y monta
# camera/build/sd con nuestros scripts + esos binarios. No se versionan binarios.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/payload.lock"

BUILD="$HERE/build"
SRC="$BUILD/upstream"
OUT="$BUILD/sd"

rm -rf "$OUT"
mkdir -p "$BUILD"
if [ ! -d "$SRC/.git" ]; then
	git clone -q "$UPSTREAM_REPO" "$SRC"
fi
git -C "$SRC" fetch -q origin "$UPSTREAM_COMMIT"
git -C "$SRC" checkout -q "$UPSTREAM_COMMIT"

HACK="$SRC/reference/sd-card-hack/anyka_hack"
cp -R "$HERE/sd" "$OUT"
mkdir -p "$OUT/anyka/bin/libre_anyka_app" "$OUT/anyka/bin/ptz"
# libre_anyka_app se compila desde el código con nuestros parches (app/build.sh);
# del paquete de jphein solo se usan sus librerías.
APP_BIN="$BUILD/app/libre_anyka_app"
[ -f "$APP_BIN" ] || "$HERE/app/build.sh"
cp "$APP_BIN" "$OUT/anyka/bin/libre_anyka_app/libre_anyka_app"
cp -R "$HACK/libre_anyka_app/lib" "$OUT/anyka/bin/libre_anyka_app/"
cp -R "$HACK/ptz/ptz_daemon_dyn" "$HACK/ptz/lib" "$OUT/anyka/bin/ptz/"
cp "$HACK/web_interface/busybox" "$OUT/anyka/bin/busybox"
chmod +x "$OUT/Factory/config.sh" "$OUT/anyka/start.sh" "$OUT/anyka/talk_session.sh" "$OUT/anyka/www/cgi-bin/ctl" \
	"$OUT/anyka/bin/libre_anyka_app/libre_anyka_app" "$OUT/anyka/bin/ptz/ptz_daemon_dyn" "$OUT/anyka/bin/busybox"

echo "Paquete listo en $OUT (upstream $UPSTREAM_COMMIT)"
