# Entorno de compilación para AK3918: la toolchain de Anyka son binarios Linux de 32 bits.
FROM debian:bookworm-slim
RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y --no-install-recommends bzip2 libc6:i386 libstdc++6:i386 zlib1g:i386 \
 && rm -rf /var/lib/apt/lists/*
COPY anyka_uclibc_gcc.tar.bz2 /tmp/
RUN tar -Pxjf /tmp/anyka_uclibc_gcc.tar.bz2 && rm /tmp/anyka_uclibc_gcc.tar.bz2
ENV PATH=/opt/arm-anykav200-crosstool/usr/bin:$PATH
WORKDIR /src
