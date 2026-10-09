#!/bin/sh
# Read-only inventory, intended for an ALREADY authorized camera shell.
# Never reads credentials, serial numbers, MAC addresses, images or cloud IDs.
printf '%s\n' '=== kernel ==='
uname -srm
printf '%s\n' '=== CPU architecture hints ==='
if [ -r /proc/cpuinfo ]; then
    sed -n '/^Processor[[:space:]]*:/p; /^model name[[:space:]]*:/p; /^CPU architecture[[:space:]]*:/p; /^Hardware[[:space:]]*:/p' /proc/cpuinfo
fi
printf '%s\n' '=== flash partition layout (no flash reads) ==='
if [ -r /proc/mtd ]; then cat /proc/mtd; fi
printf '%s\n' '=== loaded module names ==='
if [ -r /proc/modules ]; then awk '{print $1}' /proc/modules; fi
printf '%s\n' '=== relevant library filenames ==='
for dir in /lib /usr/lib /usr/custom/lib /mnt/lib; do
    for path in "$dir"/ld-* "$dir"/libc.so* "$dir"/libuClibc* "$dir"/lib*adec* "$dir"/lib*ao.so* "$dir"/libakaudio* "$dir"/libplat_common* "$dir"/libplat_ipcsrv* "$dir"/libak_mt* "$dir"/libplat_thread*; do
        [ -e "$path" ] && ls -l "$path"
    done
done
printf '%s\n' '=== available inspection commands ==='
for cmd in file readelf sha256sum netstat; do command -v "$cmd" || :; done
