#!/bin/sh
# Punto de entrada del arranque desde SD en AK3918 (firmware YI IoT).
# El firmware ejecuta /mnt/Factory/config.sh en lugar de daemon + anyka_ipc
# mientras exista esta carpeta, así que la nube de YI no arranca.
# Sin flashear nada: quitar la SD devuelve el firmware original.
PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH
exec >>/tmp/anyka-boot.log 2>&1
echo "anyka: arranque desde SD $(date)"

# Red del firmware original (wpa_supplicant + udhcpc con la config guardada).
/usr/sbin/net_manage.sh &

# Telnet de emergencia: es la única vía de acceso si algo falla.
telnetd &

# Servicios locales (vídeo, PTZ, habla, control).
/mnt/anyka/start.sh &
