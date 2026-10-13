#!/bin/sh
# Una sesión de habla: nc -e nos da el socket en stdin (G.711 A-law 8 kHz mono).
# Pasa el audio al altavoz y corta si llega EOF o si pasa 1 s sin datos: go2rtc
# deja la conexión abierta al dejar de hablar y, si el decodificador no recibe
# EOF, el altavoz repite el último trozo sin parar.
BB=/mnt/anyka/bin/busybox
FIFO=/tmp/talk.fifo
CHUNK=/tmp/talk.chunk

rm -f "$FIFO"
mkfifo "$FIFO"
ak_adec_demo 8000 1 g711a "$FIFO" >>/tmp/anyka/talk.log 2>&1 &
exec 3>"$FIFO"

# 1600 bytes = 0,2 s de audio por lectura.
while $BB timeout 1 $BB dd bs=1600 count=1 of="$CHUNK" 2>/dev/null && [ -s "$CHUNK" ]; do
	cat "$CHUNK" >&3
done

exec 3>&-
rm -f "$CHUNK"
wait
