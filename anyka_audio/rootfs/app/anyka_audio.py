#!/usr/bin/env python3
"""Anyka Bidirectional Audio Addon - Main Application."""
import os
import sys
import json
import re
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
def _get_env_str(name, default=''):
    """Read string env var with null-safe fallback."""
    raw = os.getenv(name)
    if raw in (None, "", "null", "None"):
        return default
    return str(raw)


CAMERA_IP = _get_env_str('CAMERA_IP', '')
RTSP_URL = _get_env_str('RTSP_URL', '')
CAMERAS_JSON = os.getenv('CAMERAS_JSON', '[]')
DEFAULT_TALK_MODE = "ptt"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _get_env_int(name, default):
    """Read integer env var with safe fallback."""
    raw = os.getenv(name)
    try:
        return int(raw) if raw not in (None, "", "null") else int(default)
    except (TypeError, ValueError):
        return int(default)


AUDIO_PORT = _get_env_int('AUDIO_PORT', 10000)


def _load_cameras(raw_value):
    """Load camera map from add-on config."""
    if isinstance(raw_value, list):
        cameras = raw_value
    else:
        try:
            cameras = json.loads(raw_value) if raw_value else []
        except json.JSONDecodeError:
            logger.warning("Invalid CAMERAS_JSON, ignoring")
            return {}
    camera_map = {}
    if isinstance(cameras, list):
        for item in cameras:
            if not isinstance(item, dict):
                continue
            cam_id = str(item.get('id', '')).strip()
            cam_ip = str(item.get('ip', '')).strip()
            if not cam_id or not cam_ip:
                continue
            if not re.fullmatch(r"[A-Za-z0-9_-]+", cam_id):
                logger.warning("Skipping invalid camera id: %s", cam_id)
                continue
            talk_port = item.get('talk_port', AUDIO_PORT)
            try:
                talk_port = int(talk_port)
            except (TypeError, ValueError):
                talk_port = AUDIO_PORT
            talk_mode = str(item.get('talk_mode', DEFAULT_TALK_MODE)).strip().lower()
            if talk_mode not in ("ptt", "full"):
                talk_mode = DEFAULT_TALK_MODE
            camera_map[cam_id] = {'id': cam_id, 'ip': cam_ip, 'talk_port': talk_port, 'talk_mode': talk_mode}
    return camera_map


CAMERAS = _load_cameras(CAMERAS_JSON)
if not CAMERAS:
    try:
        with open('/data/options.json', 'r', encoding='utf-8') as options_file:
            options = json.load(options_file)
        CAMERAS = _load_cameras(options.get('cameras', []))
    except (OSError, ValueError, TypeError) as exc:
        logger.debug("Could not load cameras from /data/options.json: %s", exc)
        CAMERAS = {}
DEFAULT_CAMERA_ID = next(iter(CAMERAS), None)

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
    
    def start_uplink(self, camera_ip, audio_port=10000, input_format="webm"):
        """Start uplink stream from uploaded browser/mobile chunks."""
        with self.lock:
            if self.uplink_process and self.uplink_process.poll() is None:
                logger.warning("Uplink already running")
                return False, "Uplink already running"
            
            # FFmpeg command for uplink (browser/mobile chunks -> camera TCP)
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'error',
                '-f', input_format,
                '-i', 'pipe:0',
                '-ar', '8000',          # Sample rate 8000 Hz
                '-ac', '1',             # Mono
                '-acodec', 'pcm_alaw',  # PCM A-law codec
                '-f', 'alaw',           # Output format
                f'tcp://{camera_ip}:{audio_port}'  # TCP to camera
            ]
            
            try:
                self.uplink_process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Uplink started to {camera_ip}:{audio_port} format={input_format} (PID: {self.uplink_process.pid})")
                return True, "Uplink started"
            except Exception as e:
                logger.error(f"Failed to start uplink: {e}")
                return False, str(e)

    def feed_uplink(self, audio_bytes):
        """Feed chunk to running uplink process."""
        with self.lock:
            if not self.uplink_process or self.uplink_process.poll() is not None:
                return False, "Uplink not running"
            try:
                self.uplink_process.stdin.write(audio_bytes)
                self.uplink_process.stdin.flush()
                return True, "Chunk sent"
            except Exception as e:
                logger.error("Failed to feed uplink: %s", e)
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
                stderr_text = stderr_data.decode(errors='ignore').strip()
                error_message = stderr_text or f"ffmpeg failed (return code {process.returncode})"
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
                if self.uplink_process.stdin:
                    self.uplink_process.stdin.close()
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


def resolve_camera_target(cam_id=None, camera_ip=None, audio_port=None):
    """Resolve camera target from explicit IP, cam id or defaults."""
    if camera_ip:
        return camera_ip, int(audio_port or AUDIO_PORT), None
    if cam_id and cam_id in CAMERAS:
        cam = CAMERAS[cam_id]
        return cam['ip'], int(cam.get('talk_port', AUDIO_PORT)), cam_id
    if cam_id:
        return None, None, None
    if CAMERA_IP:
        return CAMERA_IP, int(audio_port or AUDIO_PORT), None
    if DEFAULT_CAMERA_ID:
        cam = CAMERAS[DEFAULT_CAMERA_ID]
        return cam['ip'], int(cam.get('talk_port', AUDIO_PORT)), cam['id']
    return None, None, None


# API Routes
@app.route('/api/uplink/start', methods=['POST'])
def api_start_uplink():
    """Start uplink (talk to camera)."""
    data = request.get_json(silent=True) or {}
    cam_id = data.get('cam') or request.args.get('cam')
    camera_ip = data.get('camera_ip')
    audio_port = data.get('audio_port')
    input_format = data.get('input_format', 'webm')
    if audio_port is not None:
        try:
            audio_port = int(audio_port)
        except (TypeError, ValueError):
            return jsonify({'error': 'audio_port must be an integer'}), 400

    resolved_ip, resolved_port, resolved_cam = resolve_camera_target(cam_id=cam_id, camera_ip=camera_ip, audio_port=audio_port)
    if cam_id and not camera_ip and resolved_ip is None:
        return jsonify({'error': f'unknown camera id: {cam_id}'}), 400
    if not resolved_ip:
        return jsonify({'error': 'camera_ip required (or configure cameras + cam)'}), 400

    success, message = audio_manager.start_uplink(resolved_ip, resolved_port, input_format=input_format)
    if success:
        return jsonify({'status': 'started', 'message': message, 'camera_ip': resolved_ip, 'audio_port': resolved_port, 'cam': resolved_cam}), 200
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
    cam_id = request.form.get('cam') or request.args.get('cam')
    camera_ip = request.form.get('camera_ip')

    try:
        raw_port = request.form.get('audio_port')
        audio_port = int(raw_port) if raw_port else None
    except (TypeError, ValueError):
        return jsonify({'error': 'audio_port must be an integer'}), 400

    resolved_ip, resolved_port, resolved_cam = resolve_camera_target(cam_id=cam_id, camera_ip=camera_ip, audio_port=audio_port)
    if cam_id and not camera_ip and resolved_ip is None:
        return jsonify({'error': f'unknown camera id: {cam_id}'}), 400
    if not resolved_ip:
        return jsonify({'error': 'camera_ip required (or configure cameras + cam)'}), 400

    audio_file = request.files.get('audio')
    if audio_file is None:
        return jsonify({'error': 'audio file required'}), 400

    audio_bytes = audio_file.read(MAX_UPLOAD_BYTES + 1)
    if not audio_bytes:
        return jsonify({'error': 'audio file is empty'}), 400
    if len(audio_bytes) > MAX_UPLOAD_BYTES:
        return jsonify({'error': f'audio file too large (max {MAX_UPLOAD_BYTES} bytes)'}), 413

    input_format = request.form.get('input_format', 'wav')
    success, message = audio_manager.upload_uplink(resolved_ip, audio_bytes, resolved_port, input_format=input_format)
    if success:
        return jsonify({'status': 'uploaded', 'message': message, 'camera_ip': resolved_ip, 'audio_port': resolved_port, 'cam': resolved_cam}), 200
    return jsonify({'error': message}), 500


@app.route('/api/uplink/chunk', methods=['POST'])
def api_uplink_chunk():
    """Send real-time chunk to running uplink process."""
    audio_bytes = request.get_data(cache=False, as_text=False)
    if not audio_bytes:
        return jsonify({'error': 'audio chunk required'}), 400
    success, message = audio_manager.feed_uplink(audio_bytes)
    if success:
        return jsonify({'status': 'ok', 'message': message}), 200
    return jsonify({'error': message}), 409


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
    status['default_talk_mode'] = DEFAULT_TALK_MODE
    status['default_camera'] = DEFAULT_CAMERA_ID
    status['cameras'] = list(CAMERAS.values())
    return jsonify(status), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


def _render_talk_page(embedded=False):
    """Render browser/mobile talk page."""
    cameras_json = json.dumps(list(CAMERAS.values()))
    default_cam_json = json.dumps(DEFAULT_CAMERA_ID or "")
    default_talk_mode = DEFAULT_TALK_MODE
    if DEFAULT_CAMERA_ID and DEFAULT_CAMERA_ID in CAMERAS:
        default_talk_mode = CAMERAS[DEFAULT_CAMERA_ID].get('talk_mode', DEFAULT_TALK_MODE)
    embedded_json = json.dumps(bool(embedded))
    body_margin = "8px" if embedded else "20px"
    return f"""
    <html>
    <head><title>Anyka Bidirectional Audio</title></head>
    <body style="font-family: sans-serif; margin: {body_margin};">
        {'<h1>Anyka Bidirectional Audio Addon</h1>' if not embedded else ''}
        <p><strong>Talk mode:</strong> <span id="talk-mode-label">{default_talk_mode.upper()}</span></p>
        <label for="camera">Camera:</label>
        <select id="camera"></select>
        <button id="ptt">Hold to Talk</button>
        <button id="toggle">Start/Stop (FULL)</button>
        <pre id="status"></pre>
        <script>
            const cameras = {cameras_json};
            const defaultCam = {default_cam_json};
            const embedded = {embedded_json};
            const params = new URLSearchParams(window.location.search);
            const camFromQuery = params.get("cam");
            const ingressMatch = window.location.pathname.match(new RegExp("^/api/hassio_ingress/[^/]+"));
            const apiBasePath = ingressMatch ? ingressMatch[0] : "";
            const allowedOriginRaw = params.get("parent_origin");
            let allowedOrigin = "";
            if (allowedOriginRaw) {{
                try {{
                    const parsed = new URL(allowedOriginRaw);
                    if (parsed.protocol === "http:" || parsed.protocol === "https:") allowedOrigin = parsed.origin;
                }} catch (_error) {{
                    console.warn("Invalid parent_origin:", allowedOriginRaw);
                }}
            }}
            const cameraSelect = document.getElementById("camera");
            const statusEl = document.getElementById("status");
            const btnPtt = document.getElementById("ptt");
            const btnToggle = document.getElementById("toggle");
            const talkModeLabel = document.getElementById("talk-mode-label");
            let recorder = null;
            let stream = null;
            let running = false;

            const selected = camFromQuery || defaultCam || (Array.isArray(cameras) && cameras.length > 0 ? cameras[0].id : "");
            cameras.forEach((cam) => {{
                const opt = document.createElement("option");
                opt.value = cam.id;
                opt.textContent = `${{cam.id}} (${{cam.ip}}:${{cam.talk_port || 10000}})`;
                if (cam.id === selected) opt.selected = true;
                cameraSelect.appendChild(opt);
            }});
            statusEl.textContent = embedded ? "ready (embedded webview)" : "ready";
            if (embedded && !allowedOrigin) statusEl.textContent = "ready (commands disabled: set parent_origin)";
            function getCurrentTalkMode() {{
                const cam = cameras.find((item) => item.id === cameraSelect.value);
                const mode = (cam && (cam.talk_mode === "full" || cam.talk_mode === "ptt")) ? cam.talk_mode : "ptt";
                return mode === "full" ? "full" : "ptt";
            }}

            function applyTalkModeUi() {{
                const mode = getCurrentTalkMode();
                talkModeLabel.textContent = mode.toUpperCase();
                if (mode === "full") {{
                    btnPtt.style.display = "none";
                    btnToggle.style.display = "";
                }} else {{
                    btnToggle.style.display = "none";
                    btnPtt.style.display = "";
                }}
            }}

            cameraSelect.onchange = () => applyTalkModeUi();

            async function startTalk() {{
                if (running) return;
                const cam = cameraSelect.value || "";
                try {{
                    const startRes = await fetch(`${{apiBasePath}}/api/uplink/start?cam=${{encodeURIComponent(cam)}}`, {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify({{ input_format: "webm", cam }}) }});
                    const startData = await startRes.json().catch(() => ({{}}));
                    if (!startRes.ok) throw new Error(startData.error || "failed to start uplink");
                    stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    recorder = new MediaRecorder(stream, {{ mimeType: "audio/webm" }});
                    recorder.ondataavailable = async (event) => {{
                        if (!event.data || !event.data.size) return;
                        const chunkRes = await fetch(`${{apiBasePath}}/api/uplink/chunk?cam=${{encodeURIComponent(cam)}}`, {{ method: "POST", body: await event.data.arrayBuffer() }});
                        if (!chunkRes.ok) statusEl.textContent = `chunk upload failed: ${{chunkRes.status}}`;
                    }};
                    recorder.start(250);
                    running = true;
                    statusEl.textContent = `talking to cam=${{cam}}`;
                }} catch (error) {{
                    statusEl.textContent = `start failed: ${{error.message}}`;
                    await stopTalk();
                }}
            }}

            async function stopTalk() {{
                if (recorder) recorder.stop();
                if (stream) stream.getTracks().forEach((t) => t.stop());
                const stopRes = await fetch(`${{apiBasePath}}/api/uplink/stop`, {{ method: "POST" }});
                const stopData = await stopRes.json().catch(() => ({{}}));
                if (!stopRes.ok) statusEl.textContent = `stop failed: ${{stopData.error || "unknown"}}`;
                recorder = null;
                stream = null;
                running = false;
                if (stopRes.ok) statusEl.textContent = "stopped";
            }}

            btnToggle.onclick = async () => {{ if (running) await stopTalk(); else await startTalk(); }};
            btnPtt.onpointerdown = async (event) => {{ event.preventDefault(); await startTalk(); }};
            btnPtt.onpointerup = async (event) => {{ event.preventDefault(); await stopTalk(); }};
            applyTalkModeUi();

            window.addEventListener("message", async (event) => {{
                if (!embedded) return;
                if (!allowedOrigin) return;
                if (event.origin !== allowedOrigin) return;
                const data = event.data || {{}};
                if (data.type !== "anyka_talk") return;
                if (data.cam) cameraSelect.value = data.cam;
                if (data.action === "start") await startTalk();
                if (data.action === "stop") await stopTalk();
                if (data.action === "toggle") {{ if (running) await stopTalk(); else await startTalk(); }}
            }});
        </script>
    </body>
    </html>
    """


@app.route('/', methods=['GET'])
def index():
    """Index page."""
    return _render_talk_page(embedded=(request.args.get('embedded') == '1'))


@app.route('/api/uplink/webview', methods=['GET'])
def uplink_webview():
    """Embeddable webview page for dashboard cards."""
    return _render_talk_page(embedded=True)


if __name__ == '__main__':
    logger.info("Starting Anyka Bidirectional Audio Server")
    logger.info(f"Camera IP: {CAMERA_IP}")
    logger.info(f"RTSP URL: {RTSP_URL}")
    logger.info(f"Audio Port: {AUDIO_PORT}")
    logger.info(f"Default talk mode: {DEFAULT_TALK_MODE}")
    logger.info("Configured cameras: %s", ",".join(CAMERAS.keys()) if CAMERAS else "none")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=8099, debug=(LOG_LEVEL == 'DEBUG'))
