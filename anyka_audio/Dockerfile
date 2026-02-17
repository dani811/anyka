ARG BUILD_FROM
FROM $BUILD_FROM

# Install ffmpeg and required packages
RUN apk add --no-cache \
    python3 \
    ffmpeg \
    alsa-utils \
    pulseaudio \
    pulseaudio-alsa \
    py3-aiohttp \
    py3-flask \
    py3-flask-cors

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

# Copy application
COPY rootfs/ /

WORKDIR /app
CMD [ "/run.sh" ]
