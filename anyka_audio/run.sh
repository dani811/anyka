#!/usr/bin/with-contenv bashio
# ==============================================================================
# Start Anyka Bidirectional Audio addon
# ==============================================================================

bashio::log.info "Starting Anyka Bidirectional Audio addon..."

# Get configuration
export CAMERA_IP=$(bashio::config 'camera_ip')
export RTSP_URL=$(bashio::config 'rtsp_url')
export AUDIO_PORT=$(bashio::config 'audio_port')
export CAMERAS_JSON=$(bashio::config 'cameras')
export TALK_MODE=$(bashio::config 'talk_mode')
export LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Camera IP: ${CAMERA_IP}"
bashio::log.info "RTSP URL: ${RTSP_URL}"
bashio::log.info "Audio port: ${AUDIO_PORT}"
bashio::log.info "Talk mode: ${TALK_MODE}"

# Start the Python application
exec python3 /app/anyka_audio.py
