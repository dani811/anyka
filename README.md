# anyka

Minimal Home Assistant + AppDaemon project for Anyka two-way audio communication.

**Enable two-way audio streaming from Home Assistant to your Anyka IP cameras!**

## Features

- 🎤 Stream audio from your microphone to Anyka cameras
- 🏠 Native Home Assistant integration with services
- 🚀 Simple setup and configuration
- 🔧 Minimal dependencies (just ffmpeg and AppDaemon)
- 🎯 Clean and maintainable codebase

## Quick Start

### Prerequisites

- Home Assistant (2021.12+)
- AppDaemon add-on installed
- ffmpeg installed on your system
- Anyka-based IP camera on your local network

### Installation

**📖 For detailed installation instructions, see [INSTALL.md](INSTALL.md)**

Quick summary:

1. Copy `custom_components/anyka_talk/` to your Home Assistant config
2. Copy `appdaemon/apps/anyka_talk.py` and `apps.yaml` to your AppDaemon apps directory
3. Restart Home Assistant and AppDaemon
4. Use the services `anyka_talk.start` and `anyka_talk.stop`

### Basic Usage

Start streaming audio to your camera:

```yaml
service: anyka_talk.start
data:
  camera_ip: "192.168.1.100"
```

Stop the audio stream:

```yaml
service: anyka_talk.stop
```

## How It Works

### Architecture

```
┌─────────────────┐      HTTP API       ┌──────────────┐      FFmpeg        ┌─────────┐
│ Home Assistant  │ ──────────────────> │  AppDaemon   │ ────────────────> │  Camera │
│   Integration   │    (port 5050)      │    Worker    │  (TCP port 10000) │ (Anyka) │
└─────────────────┘                     └──────────────┘                    └─────────┘
        │                                       │
        │ Services:                             │ Actions:
        │ - anyka_talk.start                    │ - Capture microphone
        │ - anyka_talk.stop                     │ - Encode PCM A-law 8kHz mono
        │                                       │ - Stream via TCP
        └───────────────────────────────────────┘
```

### Components

1. **Home Assistant Custom Integration** (`custom_components/anyka_talk/`)
   - Registers services: `anyka_talk.start` and `anyka_talk.stop`
   - Communicates with AppDaemon worker via HTTP

2. **AppDaemon Worker** (`appdaemon/apps/anyka_talk.py`)
   - Exposes HTTP API endpoints: `/start`, `/stop`, `/status`
   - Manages ffmpeg process lifecycle
   - Captures audio, encodes as PCM A-law (8000Hz, mono), and streams to camera

## Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide with troubleshooting (English)
- **[INSTALL_ES.md](INSTALL_ES.md)** - Guía de instalación detallada (Español)
- **[manifest.json](custom_components/anyka_talk/manifest.json)** - Integration metadata
- **[services.yaml](custom_components/anyka_talk/services.yaml)** - Service definitions

## Examples

### Dashboard Button

Add a hold-to-talk button to your dashboard:

```yaml
type: button
name: Talk to Camera
tap_action:
  action: call-service
  service: anyka_talk.start
  data:
    camera_ip: "192.168.1.100"
hold_action:
  action: call-service
  service: anyka_talk.stop
icon: mdi:microphone
```

### Automation

Start audio when a button is toggled:

```yaml
automation:
  - alias: "Push-to-Talk"
    trigger:
      platform: state
      entity_id: input_boolean.camera_talk
    action:
      choose:
        - conditions:
            - condition: state
              entity_id: input_boolean.camera_talk
              state: "on"
          sequence:
            - service: anyka_talk.start
              data:
                camera_ip: "192.168.1.100"
        - conditions:
            - condition: state
              entity_id: input_boolean.camera_talk
              state: "off"
          sequence:
            - service: anyka_talk.stop
```

## Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Home Assistant | 2021.12+ | Core or OS |
| AppDaemon | 4.0.0+ | As add-on or standalone |
| FFmpeg | Any recent | With ALSA support |
| Python | 3.8+ | Usually included with HA |

## Troubleshooting

Common issues and solutions:

- **Services not appearing**: Check Home Assistant logs, verify file permissions, restart HA
- **FFmpeg not found**: Install ffmpeg on your system (see [INSTALL.md](INSTALL.md))
- **No audio device**: Check `arecord -L`, ensure ALSA is configured
- **Cannot connect to camera**: Verify IP address and port 10000 accessibility

For detailed troubleshooting, see [INSTALL.md](INSTALL.md#troubleshooting).

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available for use in accordance with the repository license.

## Credits

Created for the Home Assistant community to enable two-way audio communication with Anyka-based IP cameras.

## Support

- 🐛 Report bugs: [GitHub Issues](https://github.com/dani811/anyka/issues)
- 💬 Ask questions: [GitHub Discussions](https://github.com/dani811/anyka/discussions)
- 📖 Documentation: [INSTALL.md](INSTALL.md)