# Environment Configuration

## Quick Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your preferred defaults:
```bash
nano .env
# or
code .env
```

## Available Settings

### Test Duration
```bash
# Default duration in minutes (0 = manual stop)
DEFAULT_DURATION_MINUTES=5
```

### WiFi Sampling
```bash
# How often to collect WiFi metrics (in seconds)
SAMPLE_INTERVAL_SECONDS=4.0
```

### iperf3 Defaults
```bash
# Default iperf3 server (if you always use the same server)
# Leave empty to require --iperf3-server flag each time
IPERF3_SERVER=192.168.1.100

# Default port
IPERF3_PORT=5201

# Default parallel streams (recommended: 4 for WiFi testing)
IPERF3_PARALLEL=4
```

**Example:** If you set `IPERF3_SERVER=192.168.1.100` and `IPERF3_PARALLEL=4` in `.env`, then:
```bash
# This simple command:
python3 wifi_listener.py start -l "Kitchen" -a "R770" -d 5

# Will automatically use iperf3 with your defaults
# (equivalent to adding --iperf3-server 192.168.1.100 -P 4)
```

### Database & Exports
```bash
# Database path (relative to project directory)
DATABASE_PATH=data/wifi_metrics.db

# Exports directory
EXPORTS_PATH=exports
```

## Usage Examples

### Scenario 1: Always Use iperf3
If you always test with the same iperf3 server, set it in `.env`:
```bash
IPERF3_SERVER=192.168.1.100
IPERF3_PARALLEL=4
DEFAULT_DURATION_MINUTES=5
```

Then your commands become simpler:
```bash
# Upload test (uses .env defaults)
python3 wifi_listener.py start -l "Kitchen - 20ft" -a "R770"

# Override to disable iperf3 for passive test
python3 wifi_listener.py start -l "Kitchen - 20ft" -a "R770" --iperf3-server ""

# Override to use different parallel streams
python3 wifi_listener.py start -l "Kitchen - 20ft" -a "R770" -P 8
```

### Scenario 2: Sometimes Use iperf3
Leave `IPERF3_SERVER` empty in `.env`:
```bash
IPERF3_SERVER=
IPERF3_PARALLEL=4
```

Then specify server when needed:
```bash
# Passive test (no iperf3)
python3 wifi_listener.py start -l "Kitchen" -a "R770"

# Active test (iperf3 enabled, uses P=4 from .env)
python3 wifi_listener.py start -l "Kitchen" -a "R770" --iperf3-server 192.168.1.100
```

### Scenario 3: Faster Sampling
For more frequent measurements:
```bash
SAMPLE_INTERVAL_SECONDS=2.0
```

**Note:** System_profiler takes ~3-4 seconds to run, so intervals below 3 seconds may cause overlap.

## Priority

Settings are applied in this order (highest to lowest priority):
1. Command-line arguments (e.g., `-P 8`)
2. `.env` file settings
3. Built-in defaults

## Notes

- The `.env` file is ignored by git (in `.gitignore`)
- Safe to customize without affecting the repository
- Changes take effect immediately (no restart needed)
- Invalid values fall back to built-in defaults
