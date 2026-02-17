"""AppDaemon app for Anyka Two-Way Audio."""
import appdaemon.plugins.hass.hassapi as hass
import subprocess
import threading
import logging


class AnykaTalk(hass.Hass):
    """AppDaemon worker for Anyka audio streaming."""
    
    def initialize(self):
        """Initialize the app."""
        self.log("Initializing Anyka Talk worker")
        self.ffmpeg_process = None
        self.stream_lock = threading.Lock()
        
        # Register HTTP endpoints
        self.register_endpoint(self.start_endpoint, "start")
        self.register_endpoint(self.stop_endpoint, "stop")
        self.register_endpoint(self.status_endpoint, "status")
        
        self.log("Anyka Talk worker initialized")
    
    def start_endpoint(self, data):
        """Handle POST /start endpoint."""
        try:
            camera_ip = data.get("camera_ip")
            if not camera_ip:
                return {"error": "camera_ip required"}, 400
            
            with self.stream_lock:
                if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                    self.log("Stream already running")
                    return {"status": "already_running"}, 200
                
                self.log(f"Starting audio stream to {camera_ip}")
                self.start_stream(camera_ip)
                
            return {"status": "started", "camera_ip": camera_ip}, 200
            
        except Exception as e:
            self.log(f"Error in start endpoint: {e}", level="ERROR")
            return {"error": str(e)}, 500
    
    def stop_endpoint(self, data):
        """Handle POST /stop endpoint."""
        try:
            with self.stream_lock:
                if not self.ffmpeg_process or self.ffmpeg_process.poll() is not None:
                    self.log("No stream running")
                    return {"status": "not_running"}, 200
                
                self.log("Stopping audio stream")
                self.stop_stream()
                
            return {"status": "stopped"}, 200
            
        except Exception as e:
            self.log(f"Error in stop endpoint: {e}", level="ERROR")
            return {"error": str(e)}, 500
    
    def status_endpoint(self, data):
        """Handle GET /status endpoint."""
        try:
            with self.stream_lock:
                if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                    status = "running"
                else:
                    status = "stopped"
            
            return {"status": status}, 200
            
        except Exception as e:
            self.log(f"Error in status endpoint: {e}", level="ERROR")
            return {"error": str(e)}, 500
    
    def start_stream(self, camera_ip):
        """Start ffmpeg audio stream to camera."""
        # ffmpeg command to capture microphone, encode as pcm_alaw 8000Hz mono
        # and send raw stream via TCP to camera port 10000
        cmd = [
            "ffmpeg",
            "-f", "alsa",  # Input from ALSA (Linux audio)
            "-i", "default",  # Default microphone
            "-ar", "8000",  # Sample rate 8000 Hz
            "-ac", "1",  # Mono audio (1 channel)
            "-acodec", "pcm_alaw",  # Encode as PCM A-law
            "-f", "alaw",  # Output format
            f"tcp://{camera_ip}:10000"  # Send to camera via TCP
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log(f"ffmpeg process started with PID {self.ffmpeg_process.pid}")
        except Exception as e:
            self.log(f"Failed to start ffmpeg: {e}", level="ERROR")
            raise
    
    def stop_stream(self):
        """Stop ffmpeg audio stream."""
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
                self.log("ffmpeg process terminated")
            except subprocess.TimeoutExpired:
                self.log("ffmpeg didn't terminate, killing it", level="WARNING")
                self.ffmpeg_process.kill()
                self.ffmpeg_process.wait()
            finally:
                self.ffmpeg_process = None
    
    def terminate(self):
        """Clean up on app termination."""
        self.log("Terminating Anyka Talk worker")
        with self.stream_lock:
            if self.ffmpeg_process:
                self.stop_stream()
