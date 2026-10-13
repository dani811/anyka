#!/bin/sh
# Instala camera/build/sd en la SD de la cámara por FTP (ftpd del firmware, root sin
# contraseña). Antes guarda una copia de /mnt/Factory/config.sh en camera/backups/.
# Uso: camera/install.sh <ip-camara>
set -eu

IP=${1:?uso: $0 <ip-camara>}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$HERE/build/sd"
FTP="ftp://$IP"
[ -d "$OUT" ] || { echo "Falta $OUT: ejecuta antes camera/fetch-payload.sh" >&2; exit 1; }

mkdir -p "$HERE/backups"
BK="$HERE/backups/config.sh.$IP.$(date +%Y%m%d-%H%M%S)"
if curl -sf --max-time 20 -u root: "$FTP/mnt/Factory/config.sh" -o "$BK"; then
	echo "Copia de seguridad: $BK"
else
	echo "Aviso: no había /mnt/Factory/config.sh que copiar" >&2
	rm -f "$BK"
fi

cd "$OUT"
find . -type f | sed 's|^\./||' | while read -r f; do
	curl -sf --max-time 120 --ftp-create-dirs -u root: -T "$f" "$FTP/mnt/$f" || { echo "FALLO al subir $f" >&2; exit 1; }
done
echo "Subido. Reinicia la cámara para aplicar."
