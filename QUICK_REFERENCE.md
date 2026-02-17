# Quick Reference - Anyka Bidirectional Audio

## Installation

```bash
# 1. Add repository to HAOS
Supervisor → Add-on Store → ⋮ → Repositories
→ https://github.com/dani811/anyka

# 2. Install "Anyka Bidirectional Audio" addon

# 3. Configure addon (optional)
camera_ip: "192.168.1.100"
rtsp_url: "rtsp://192.168.1.100:554/audio"

# 4. Start addon

# 5. Add to configuration.yaml
anyka_audio:

# 6. Restart Home Assistant
```

## Services

### Talk (Uplink)
```yaml
# Start
service: anyka_audio.start_talk
data:
  camera_ip: "192.168.1.100"
  audio_port: 10000  # optional

# Stop
service: anyka_audio.stop_talk
```

### Listen (Downlink)
```yaml
# Start
service: anyka_audio.start_listen
data:
  rtsp_url: "rtsp://192.168.1.100:554/audio"

# Stop
service: anyka_audio.stop_listen
```

## Automations

### Push-to-Talk
```yaml
automation:
  - alias: "Start Talk"
    trigger:
      platform: state
      entity_id: input_boolean.talk
      to: "on"
    action:
      service: anyka_audio.start_talk
      data:
        camera_ip: "192.168.1.100"

  - alias: "Stop Talk"
    trigger:
      platform: state
      entity_id: input_boolean.talk
      to: "off"
    action:
      service: anyka_audio.stop_talk
```

### Bidirectional Intercom
```yaml
automation:
  - alias: "Start Intercom"
    trigger:
      platform: state
      entity_id: input_boolean.intercom
      to: "on"
    action:
      - service: anyka_audio.start_talk
        data:
          camera_ip: "192.168.1.100"
      - service: anyka_audio.start_listen
        data:
          rtsp_url: "rtsp://192.168.1.100:554/audio"

  - alias: "Stop Intercom"
    trigger:
      platform: state
      entity_id: input_boolean.intercom
      to: "off"
    action:
      - service: anyka_audio.stop_talk
      - service: anyka_audio.stop_listen
```

## Dashboard Cards

### Talk Button
```yaml
type: button
name: Talk
tap_action:
  action: call-service
  service: anyka_audio.start_talk
  data:
    camera_ip: "192.168.1.100"
hold_action:
  action: call-service
  service: anyka_audio.stop_talk
icon: mdi:microphone
```

### Listen Toggle
```yaml
type: button
name: Listen
tap_action:
  action: call-service
  service: anyka_audio.start_listen
  data:
    rtsp_url: "rtsp://192.168.1.100:554/audio"
hold_action:
  action: call-service
  service: anyka_audio.stop_listen
icon: mdi:speaker
```

## API Endpoints

```bash
# Base URL: http://localhost:8099

# Start talk
curl -X POST http://localhost:8099/api/uplink/start \
  -H "Content-Type: application/json" \
  -d '{"camera_ip": "192.168.1.100", "audio_port": 10000}'

# Stop talk
curl -X POST http://localhost:8099/api/uplink/stop

# Start listen
curl -X POST http://localhost:8099/api/downlink/start \
  -H "Content-Type: application/json" \
  -d '{"rtsp_url": "rtsp://192.168.1.100:554/audio"}'

# Stop listen
curl -X POST http://localhost:8099/api/downlink/stop

# Get status
curl http://localhost:8099/api/status

# Health check
curl http://localhost:8099/health
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Services not showing | Check addon is running, restart HA |
| No audio output | Verify RTSP URL, check logs |
| No audio input | Verify camera IP/port, check network |
| Connection failed | Check firewall, test with curl |

## Configuration Options

```yaml
# In addon configuration tab
camera_ip: "192.168.1.100"      # Optional, can be set per call
rtsp_url: "rtsp://IP:554/audio" # Optional, can be set per call
audio_port: 10000               # TCP port for uplink
log_level: info                 # trace|debug|info|warning|error
```

## Common RTSP URLs

```
# Standard RTSP
rtsp://192.168.1.100:554/audio
rtsp://192.168.1.100:554/stream1

# With authentication
rtsp://username:password@192.168.1.100:554/audio

# Custom port
rtsp://192.168.1.100:8554/audio
```

## Technical Details

**Uplink (Talk):**
- Format: PCM A-law
- Sample rate: 8000 Hz
- Channels: Mono (1)
- Transport: TCP
- Port: 10000 (default)

**Downlink (Listen):**
- Source: RTSP stream
- Format: Auto-detected
- Transport: RTSP (TCP)
- Port: 554 (typical)

**Addon:**
- Container port: 8099/tcp
- Base: Alpine Linux 3.19
- Audio: ALSA + PulseAudio
- FFmpeg: Included

## Files

- `/config/addons/local_anyka_audio/` - Addon location
- Logs: Supervisor → Anyka Bidirectional Audio → Log
- Config: Supervisor → Anyka Bidirectional Audio → Configuration

## Support

- Docs: [anyka_audio/README.md](anyka_audio/README.md)
- Issues: https://github.com/dani811/anyka/issues
- Changelog: [CHANGELOG.md](CHANGELOG.md)
