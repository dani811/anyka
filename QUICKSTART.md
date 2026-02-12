# Quick Start Guide

## Installation in 5 Minutes

### 1. Copy Integration Files

```bash
# SSH or access your Home Assistant config directory
cd /config

# Create and copy custom integration
mkdir -p custom_components/anyka_talk
# Copy __init__.py, manifest.json, services.yaml to this directory
```

### 2. Copy AppDaemon Files

```bash
# Copy to AppDaemon apps directory
cd /config/appdaemon/apps
# Copy anyka_talk.py and apps.yaml
```

### 3. Restart

- Restart Home Assistant
- Restart AppDaemon

### 4. Test

In Home Assistant Developer Tools → Services:

```yaml
service: anyka_talk.start
data:
  camera_ip: "YOUR_CAMERA_IP"
```

## Need Help?

- **Detailed Instructions**: See [INSTALL.md](INSTALL.md) (English) or [INSTALL_ES.md](INSTALL_ES.md) (Español)
- **Troubleshooting**: Check the troubleshooting sections in the installation guides
- **Issues**: [GitHub Issues](https://github.com/dani811/anyka/issues)

## Common Issues

| Problem | Solution |
|---------|----------|
| Services not showing | Check logs, verify file permissions, restart HA |
| FFmpeg not found | Install ffmpeg: `apk add ffmpeg` (HA OS) |
| No audio device | Check `arecord -L`, configure ALSA |
| Can't connect to camera | Verify IP and port 10000 is open |

---

**Full documentation**: [INSTALL.md](INSTALL.md) | **Español**: [INSTALL_ES.md](INSTALL_ES.md)
