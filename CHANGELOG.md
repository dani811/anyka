# Changelog

All notable changes to this project will be documented in this file.

## [2.0.4] - 2026-02-18

### Changed
- Add-on version bump to `2.0.4` for Home Assistant update detection
- Internal add-on integration manifest version bump to `2.0.4`

## [2.0.3] - 2026-02-18

### Changed
- Simplified addon configuration to use `cameras` as the primary camera list (supports one or many cameras)
- Added optional per-camera `talk_mode` (`ptt` / `full`) in addon camera configuration
- Camera loading now falls back to `/data/options.json` when environment camera list is empty (aligned with Home Assistant addon options storage)
- Add-on version bump to `2.0.3` for Home Assistant update detection
- Internal add-on integration manifest version bump to `2.0.3`

## [2.0.2] - 2026-02-18

### Changed
- Add-on schema now accepts `cameras` configurations without requiring root `audio_port`
- Add-on version bump to `2.0.2` for Home Assistant update detection
- Internal add-on integration manifest version bump to `2.0.2`

## [2.0.1] - 2026-02-18

### Added
- Add-on Ingress panel metadata so UI opens via Home Assistant "OPEN WEB UI"
- Embedded webview endpoint and command-style browser talk controls

### Changed
- Add-on version bump to `2.0.1` to allow Home Assistant update detection
- Internal add-on integration manifest version bump to `2.0.1`

## [2.0.0] - 2026-02-17

### 🎯 Major Refactor: HAOS Monorepo with Bidirectional Audio

#### Added
- **HAOS Native Addon** (`anyka_audio/`)
  - Self-contained Docker container with all dependencies
  - Multi-architecture support (aarch64, amd64, armhf, armv7, i386)
  - Integrated ffmpeg and Python server
  - Visual assets (icon.svg, logo.svg)
  
- **Bidirectional Audio Support**
  - **Uplink (Talk)**: Microphone → Camera via TCP (existing functionality)
  - **Downlink (Listen)**: Camera → Speaker via RTSP (NEW!)
  - Simultaneous bidirectional communication support
  
- **New Services**
  - `anyka_audio.start_talk` - Start uplink (replaces `anyka_talk.start`)
  - `anyka_audio.stop_talk` - Stop uplink (replaces `anyka_talk.stop`)
  - `anyka_audio.start_listen` - Start downlink (NEW!)
  - `anyka_audio.stop_listen` - Stop downlink (NEW!)
  
- **Flask API Server**
  - REST API on port 8099
  - 6 endpoints for audio control
  - Health check endpoint
  - Thread-safe audio stream management
  
- **Comprehensive Documentation**
  - Complete addon README with examples
  - Updated main README for v2.0
  - Installation guides
  - Troubleshooting section
  - Automation examples

#### Changed
- **Architecture**: Migrated from AppDaemon to HAOS addon
- **Installation**: Simplified to 3 steps (add repo, install, configure)
- **Integration domain**: Changed from `anyka_talk` to `anyka_audio`
- **Service names**: More descriptive (start_talk, stop_talk, etc.)

#### Removed
- **AppDaemon dependency** - No longer needed
- **Manual file copying** - Everything is self-contained in addon
- **Complex setup** - Now a simple addon installation

#### Deprecated
- `custom_components/anyka_talk/` - Kept for legacy compatibility
- `appdaemon/apps/` - Kept for reference, no longer maintained
- v1.0 documentation - Marked as deprecated in README

### Technical Details

**Container Stack:**
- Base: Alpine Linux 3.19
- Python 3 with Flask, aiohttp
- FFmpeg with ALSA support
- PulseAudio for audio routing

**Audio Processing:**
- Uplink: ALSA → FFmpeg → PCM A-law 8kHz mono → TCP
- Downlink: RTSP → FFmpeg → ALSA speaker

**Communication:**
- Home Assistant ↔ Addon: HTTP API (port 8099)
- Addon ↔ Camera Uplink: TCP (port 10000)
- Addon ↔ Camera Downlink: RTSP (typically port 554)

## [1.0.0] - 2026-02-12

### Initial Release

#### Added
- Home Assistant custom integration (`custom_components/anyka_talk/`)
- AppDaemon worker for audio streaming
- Uplink (talk) functionality only
- TCP audio streaming to Anyka cameras
- PCM A-law encoding at 8kHz mono
- Basic documentation (README, INSTALL.md, INSTALL_ES.md)
- Services: `anyka_talk.start` and `anyka_talk.stop`

#### Features
- Manual installation via file copying
- AppDaemon HTTP API
- FFmpeg-based audio capture and encoding
- Thread-safe process management

---

## Migration Guide: v1.0 → v2.0

### For Existing Users

If you're upgrading from v1.0:

1. **Backup your configuration** (optional, for reference)
   
2. **Install the new addon**:
   - Add repository to HAOS
   - Install "Anyka Bidirectional Audio"
   - Configure camera_ip and rtsp_url
   - Start the addon

3. **Update your configuration.yaml**:
   ```yaml
   # Remove (v1.0):
   # anyka_talk:
   
   # Add (v2.0):
   anyka_audio:
   ```

4. **Update automations and scripts**:
   - Replace `anyka_talk.start` → `anyka_audio.start_talk`
   - Replace `anyka_talk.stop` → `anyka_audio.stop_talk`
   - Add `anyka_audio.start_listen` for downlink audio
   - Add `anyka_audio.stop_listen` to stop downlink

5. **Remove old components** (optional):
   - Can remove AppDaemon worker files
   - Can remove old custom_components/anyka_talk/
   - Legacy files kept in repo for reference

### Example Migration

**v1.0 Automation:**
```yaml
service: anyka_talk.start
data:
  camera_ip: "192.168.1.100"
```

**v2.0 Equivalent:**
```yaml
service: anyka_audio.start_talk
data:
  camera_ip: "192.168.1.100"
```

**v2.0 with Bidirectional:**
```yaml
# Talk AND listen
- service: anyka_audio.start_talk
  data:
    camera_ip: "192.168.1.100"
- service: anyka_audio.start_listen
  data:
    rtsp_url: "rtsp://192.168.1.100:554/audio"
```

---

For more information, see:
- [README.md](README.md) - Main documentation
- [anyka_audio/README.md](anyka_audio/README.md) - Addon documentation
- [GitHub Issues](https://github.com/dani811/anyka/issues) - Support
