#!/usr/bin/env python3
"""Loopback-only go2rtc -> ffmpeg -> raw PCMA test. No camera or microphone.
Usage: python3 tests/check_go2rtc_transport.py /path/to/go2rtc
Requires ffmpeg on PATH. Not a hardware or browser/WebRTC validation.
"""
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    binary = str(Path(sys.argv[1]).resolve())
    received = bytearray()
    with tempfile.TemporaryDirectory() as tmp, socket.socket() as sink:
        sink.bind(("127.0.0.1", 0))
        sink.listen(1)
        sink.settimeout(12)
        sink_port = sink.getsockname()[1]
        with socket.socket() as api:
            api.bind(("127.0.0.1", 0))
            api_port = api.getsockname()[1]
        with socket.socket() as rtsp:
            rtsp.bind(("127.0.0.1", 0))
            rtsp_port = rtsp.getsockname()[1]
        errors = []
        def collect():
            try:
                conn, _ = sink.accept()
                with conn:
                    conn.settimeout(12)
                    while len(received) < 16000:
                        chunk = conn.recv(min(4096, 16000 - len(received)))
                        if not chunk: break
                        received.extend(chunk)
            except Exception as exc:
                errors.append(str(exc))
        thread = threading.Thread(target=collect, daemon=True)
        thread.start()
        # Source is generated silence, explicitly PCMA/8000 in a WAV container.
        source = (f'exec:{ffmpeg} -hide_banner -loglevel error -re -f lavfi '
                  '-i anullsrc=r=8000:cl=mono -c:a pcm_alaw -f wav pipe:1')
        target = (f'exec:{ffmpeg} -hide_banner -loglevel error -probesize 32 -analyzeduration 0 '
                  '-f alaw -ar 8000 -ac 1 -i pipe:0 -map 0:a:0 -c:a copy '
                  f'-f alaw -flush_packets 1 tcp://127.0.0.1:{sink_port}'
                  '#backchannel=1#audio=alaw/8000')
        config = Path(tmp) / "go2rtc.yaml"
        config.write_text('api:\n  listen: "127.0.0.1:%s"\nrtsp:\n  listen: "127.0.0.1:%s"\n'
                          'webrtc:\n  listen: ""\nstreams:\n  silence:\n    - %s\n  sink:\n    - %s\n'
                          % (api_port, rtsp_port, json.dumps(source), json.dumps(target)))
        log_path = Path(tmp) / "go2rtc.log"
        with log_path.open("wb") as log:
            proc = subprocess.Popen([binary, "-config", str(config)], stdout=log, stderr=log)
            try:
                base = f"http://127.0.0.1:{api_port}"
                for _ in range(100):
                    try:
                        with urllib.request.urlopen(base + "/api/streams", timeout=.2) as response:
                            response.read()
                        break
                    except OSError:
                        if proc.poll() is not None: raise RuntimeError(log_path.read_text())
                        time.sleep(.05)
                url = base + "/api/streams?" + urllib.parse.urlencode({"src": f"rtsp://127.0.0.1:{rtsp_port}/silence", "dst": "sink"})
                with urllib.request.urlopen(urllib.request.Request(url, method="POST"), timeout=10) as response:
                    state = json.load(response)
                thread.join(timeout=12)
                if thread.is_alive() or errors:
                    raise AssertionError(f"capture incomplete: {errors}")
                if len(received) != 16000 or set(received) != {0xD5}:
                    raise AssertionError(f"expected 16000 PCMA silence bytes, got {len(received)}; values={set(received)}")
                print(json.dumps({"result": "pass", "pcma_bytes": len(received),
                                  "rate": 8000, "seconds": 2,
                                  "scope": "go2rtc exec + ffmpeg + loopback TCP; no hardware/WebRTC"}))
            except Exception as exc:
                if isinstance(exc, urllib.error.HTTPError): print(exc.read().decode(), file=sys.stderr)
                print(log_path.read_text(), file=sys.stderr)
                raise
            finally:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()

if __name__ == "__main__":
    main()
