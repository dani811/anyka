#!/usr/bin/env python3
"""Anyka Bidirectional Audio Addon - Main Application."""
import os
import sys
import json
import logging
import subprocess
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
CAMERA_IP = os.getenv('CAMERA_IP', '')
RTSP_URL = os.getenv('RTSP_URL', '')
AUDIO_PORT = int(os.getenv('AUDIO_PORT', '10000'))

# Flask app
app = Flask(__name__)
CORS(app)

# Global state
uplink_process = None  # Talk to camera (microphone -> camera)
downlink_process = None  # Listen from camera (camera -> speaker)
process_lock = threading.Lock()


class AudioManager:
    """Manage bidirectional audio streams."""
    
    def __init__(self):
        self.uplink_process = None
        self.downlink_process = None
        self.lock = threading.Lock()
    
    def start_uplink(self, camera_ip, audio_port=10000):
        """Start uplink audio stream (microphone -> camera via TCP)."""
        with self.lock:
            if self.uplink_process and self.uplink_process.poll() is None:
                logger.warning("Uplink already running")
                return False, "Uplink already running"
            
            # FFmpeg command for uplink (talk)
            cmd = [
                'ffmpeg',
                '-f', 'alsa',           # Input from ALSA
                '-i', 'default',        # Default microphone
                '-ar', '8000',          # Sample rate 8000 Hz
                '-ac', '1',             # Mono
                '-acodec', 'pcm_alaw',  # PCM A-law codec
                '-f', 'alaw',           # Output format
                f'tcp://{camera_ip}:{audio_port}'  # TCP to camera
            ]
            
            try:
                self.uplink_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Uplink started to {camera_ip}:{audio_port} (PID: {self.uplink_process.pid})")
                return True, "Uplink started"
            except Exception as e:
                logger.error(f"Failed to start uplink: {e}")
                return False, str(e)

    def upload_uplink(self, camera_ip, audio_bytes, audio_port=10000, input_format="wav"):
        """Upload audio bytes and stream them to camera via TCP."""
        with self.lock:
            if self.uplink_process and self.uplink_process.poll() is None:
                logger.warning("Uplink already running")
                return False, "Uplink already running"

            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'error',
                '-f', input_format,
                '-i', 'pipe:0',
                '-ar', '8000',
                '-ac', '1',
                '-acodec', 'pcm_alaw',
                '-f', 'alaw',
                f'tcp://{camera_ip}:{audio_port}'
            ]

            try:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, stderr_data = process.communicate(input=audio_bytes, timeout=60)
                if process.returncode == 0:
                    logger.info(f"Uploaded uplink sent to {camera_ip}:{audio_port}")
                    return True, "Uploaded uplink sent"
                error_message = stderr_data.decode(errors='ignore').strip() or "ffmpeg failed"
                logger.error("Upload uplink failed: %s", error_message)
                return False, error_message
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                logger.error("Upload uplink timed out")
                return False, "Upload uplink timed out"
            except Exception as e:
                logger.error(f"Failed to upload uplink: {e}")
                return False, str(e)
    
    def stop_uplink(self):
        """Stop uplink audio stream."""
        with self.lock:
            if not self.uplink_process or self.uplink_process.poll() is not None:
                logger.info("No uplink running")
                return False, "No uplink running"
            
            try:
                self.uplink_process.terminate()
                self.uplink_process.wait(timeout=5)
                logger.info("Uplink stopped")
                self.uplink_process = None
                return True, "Uplink stopped"
            except subprocess.TimeoutExpired:
                logger.warning("Uplink didn't terminate, killing")
                self.uplink_process.kill()
                self.uplink_process.wait()
                self.uplink_process = None
                return True, "Uplink killed"
            except Exception as e:
                logger.error(f"Failed to stop uplink: {e}")
                return False, str(e)
    
    def start_downlink(self, rtsp_url):
        """Start downlink audio stream (camera RTSP -> speaker)."""
        with self.lock:
            if self.downlink_process and self.downlink_process.poll() is None:
                logger.warning("Downlink already running")
                return False, "Downlink already running"
            
            # FFmpeg command for downlink (listen)
            cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',  # Use TCP for RTSP
                '-i', rtsp_url,            # RTSP input from camera
                '-f', 'alsa',              # Output to ALSA
                '-ar', '8000',             # Sample rate 8000 Hz
                '-ac', '1',                # Mono
                'default'                  # Default speaker
            ]
            
            try:
                self.downlink_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Downlink started from {rtsp_url} (PID: {self.downlink_process.pid})")
                return True, "Downlink started"
            except Exception as e:
                logger.error(f"Failed to start downlink: {e}")
                return False, str(e)
    
    def stop_downlink(self):
        """Stop downlink audio stream."""
        with self.lock:
            if not self.downlink_process or self.downlink_process.poll() is not None:
                logger.info("No downlink running")
                return False, "No downlink running"
            
            try:
                self.downlink_process.terminate()
                self.downlink_process.wait(timeout=5)
                logger.info("Downlink stopped")
                self.downlink_process = None
                return True, "Downlink stopped"
            except subprocess.TimeoutExpired:
                logger.warning("Downlink didn't terminate, killing")
                self.downlink_process.kill()
                self.downlink_process.wait()
                self.downlink_process = None
                return True, "Downlink killed"
            except Exception as e:
                logger.error(f"Failed to stop downlink: {e}")
                return False, str(e)
    
    def get_status(self):
        """Get current status of audio streams."""
        with self.lock:
            return {
                'uplink': 'running' if self.uplink_process and self.uplink_process.poll() is None else 'stopped',
                'downlink': 'running' if self.downlink_process and self.downlink_process.poll() is None else 'stopped'
            }


# Initialize audio manager
audio_manager = AudioManager()


# API Routes
@app.route('/api/uplink/start', methods=['POST'])
def api_start_uplink():
    """Start uplink (talk to camera)."""
    data = request.get_json() or {}
    camera_ip = data.get('camera_ip', CAMERA_IP)
    audio_port = data.get('audio_port', AUDIO_PORT)
    
    if not camera_ip:
        return jsonify({'error': 'camera_ip required'}), 400
    
    success, message = audio_manager.start_uplink(camera_ip, audio_port)
    if success:
        return jsonify({'status': 'started', 'message': message}), 200
    else:
        return jsonify({'error': message}), 500


@app.route('/api/uplink/stop', methods=['POST'])
def api_stop_uplink():
    """Stop uplink."""
    success, message = audio_manager.stop_uplink()
    if success:
        return jsonify({'status': 'stopped', 'message': message}), 200
    else:
        return jsonify({'error': message}), 200


@app.route('/api/uplink/upload', methods=['POST'])
def api_upload_uplink():
    """Upload and stream audio bytes to camera (no URL dependency)."""
    camera_ip = request.form.get('camera_ip', CAMERA_IP)
    if not camera_ip:
        return jsonify({'error': 'camera_ip required'}), 400

    try:
        audio_port = int(request.form.get('audio_port', AUDIO_PORT))
    except (TypeError, ValueError):
        return jsonify({'error': 'audio_port must be an integer'}), 400

    audio_file = request.files.get('audio')
    if audio_file is None:
        return jsonify({'error': 'audio file required'}), 400

    audio_bytes = audio_file.read()
    if not audio_bytes:
        return jsonify({'error': 'audio file is empty'}), 400

    input_format = request.form.get('input_format', 'wav')
    success, message = audio_manager.upload_uplink(camera_ip, audio_bytes, audio_port, input_format=input_format)
    if success:
        return jsonify({'status': 'uploaded', 'message': message}), 200
    return jsonify({'error': message}), 500


@app.route('/api/downlink/start', methods=['POST'])
def api_start_downlink():
    """Start downlink (listen from camera)."""
    data = request.get_json() or {}
    rtsp_url = data.get('rtsp_url', RTSP_URL)
    
    if not rtsp_url:
        return jsonify({'error': 'rtsp_url required'}), 400
    
    success, message = audio_manager.start_downlink(rtsp_url)
    if success:
        return jsonify({'status': 'started', 'message': message}), 200
    else:
        return jsonify({'error': message}), 500


@app.route('/api/downlink/stop', methods=['POST'])
def api_stop_downlink():
    """Stop downlink."""
    success, message = audio_manager.stop_downlink()
    if success:
        return jsonify({'status': 'stopped', 'message': message}), 200
    else:
        return jsonify({'error': message}), 200


@app.route('/api/status', methods=['GET'])
def api_status():
    """Get status of audio streams."""
    status = audio_manager.get_status()
    return jsonify(status), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@app.route('/', methods=['GET'])
def index():
    """Index page."""
    return """
    <html>
    <head><title>Anyka Bidirectional Audio</title></head>
    <body>
        <h1>Anyka Bidirectional Audio Addon</h1>
        <p>API Endpoints:</p>
        <ul>
            <li>POST /api/uplink/start - Start talk (mic -> camera)</li>
            <li>POST /api/uplink/stop - Stop talk</li>
            <li>POST /api/downlink/start - Start listen (camera -> speaker)</li>
            <li>POST /api/downlink/stop - Stop listen</li>
            <li>GET /api/status - Get stream status</li>
        </ul>
    </body>
    </html>
    """


if __name__ == '__main__':
    logger.info("Starting Anyka Bidirectional Audio Server")
    logger.info(f"Camera IP: {CAMERA_IP}")
    logger.info(f"RTSP URL: {RTSP_URL}")
    logger.info(f"Audio Port: {AUDIO_PORT}")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=8099, debug=(LOG_LEVEL == 'DEBUG'))
