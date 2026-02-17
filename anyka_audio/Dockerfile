ARG BUILD_FROM
FROM $BUILD_FROM

# Install ffmpeg and required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    alsa-utils \
    pulseaudio \
    pulseaudio-alsa \
    && pip3 install --no-cache-dir \
    aiohttp \
    flask \
    flask-cors

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

# Copy application
COPY rootfs/ /

WORKDIR /app
CMD [ "/run.sh" ]
