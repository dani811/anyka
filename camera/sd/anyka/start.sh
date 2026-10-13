#!/bin/sh
# Arranca y vigila los servicios locales de la cámara. Lo lanza Factory/config.sh.
# Cada servicio corre en un bucle que lo relanza si se cae.
BASE=/mnt/anyka
. "$BASE/anyka.conf"
LOG=/tmp/anyka
mkdir -p "$LOG"

log() { echo "$(date '+%H:%M:%S') $*" >>"$LOG/start.log"; }

# Vídeo + micrófono: RTSP en :554 (/vs0 720p, /vs1 sub) y foto en :3000/snapshot.jpeg.
video_loop() {
	while true; do
		log "video: start"
		( cd /tmp && LD_LIBRARY_PATH="$BASE/bin/libre_anyka_app/lib" \
			"$BASE/bin/libre_anyka_app/libre_anyka_app" \
			-w "$VIDEO_SUB_WIDTH" -h "$VIDEO_SUB_HEIGHT" -m 0 -i 4 -u ) >>"$LOG/video.log" 2>&1
		log "video: exit $?"
		sleep 5
	done
}

# Motores e IR-cut: lee órdenes de la FIFO /tmp/ptz.daemon.
ptz_loop() {
	while true; do
		log "ptz: start"
		LD_LIBRARY_PATH="$BASE/bin/ptz/lib" "$BASE/bin/ptz/ptz_daemon_dyn" >>"$LOG/ptz.log" 2>&1
		log "ptz: exit $?"
		sleep 5
	done
}

ptz_init() {
	# Espera a que el daemon cree su FIFO antes de mandar órdenes.
	i=0
	while [ ! -p /tmp/ptz.daemon ] && [ $i -lt 30 ]; do sleep 1; i=$((i + 1)); done
	[ -p /tmp/ptz.daemon ] || { log "ptz: sin FIFO"; return; }
	[ "$PTZ_HOME_ON_BOOT" = 1 ] && echo init_ptz >/tmp/ptz.daemon
	echo init_ir >/tmp/ptz.daemon
}

# Habla: audio G.711 A-law 8 kHz por TCP -> altavoz. Una conexión cada vez;
# el decodificador se rearma después de cada envío.
talk_loop() {
	rm -f /tmp/talk.fifo
	mkfifo /tmp/talk.fifo
	while true; do
		ak_adec_demo 8000 1 g711a /tmp/talk.fifo >>"$LOG/talk.log" 2>&1 &
		nc -l -p "$TALK_PORT" >/tmp/talk.fifo
		sleep 1
	done
}

# API de control HTTP (PTZ, IR, LEDs, estado).
ctl_start() {
	conf=/tmp/anyka-httpd.conf
	if [ -n "$CTL_ALLOW_IP" ]; then
		printf 'A:%s\nA:127.0.0.1\nD:*\n' "$CTL_ALLOW_IP" >"$conf"
	else
		: >"$conf"
	fi
	"$BASE/bin/busybox" httpd -p "$CTL_PORT" -h "$BASE/www" -c "$conf"
	log "ctl: httpd en :$CTL_PORT"
}

# libre_anyka_app necesita el driver de cámara que carga /usr/sbin/camera.sh en rc.local.
sleep 10
video_loop &
ptz_loop &
ptz_init &
talk_loop &
ctl_start
