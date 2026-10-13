#!/bin/sh
# Restaura en la cámara un /mnt/Factory/config.sh guardado por install.sh.
# Uso: camera/rollback.sh <ip-camara> <camera/backups/config.sh.IP.FECHA>
# Para volver al firmware original de YI basta con sacar la SD.
set -eu

IP=${1:?uso: $0 <ip-camara> <copia>}
BK=${2:?uso: $0 <ip-camara> <copia>}
[ -f "$BK" ] || { echo "No existe $BK" >&2; exit 1; }
curl -sf --max-time 20 -u root: -T "$BK" "ftp://$IP/mnt/Factory/config.sh"
echo "Restaurado $BK. Reinicia la cámara para aplicar."
