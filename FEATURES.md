# WiFi Listener - Features Overview

## Core Features

### WiFi Monitoring
- ✅ Real-time WiFi metrics collection every 4 seconds
- ✅ Captures: Signal (RSSI), Noise, SNR, TX Rate, Channel, MCS, PHY Mode
- ✅ macOS system_profiler integration (no root required)
- ✅ Graceful Ctrl+C handling
- ✅ Auto-stop with configurable duration

### Data Storage
- ✅ SQLite database for all measurements
- ✅ Session-based organization
- ✅ Tracks location, AP name, test parameters
- ✅ Timestamps for time-series analysis

### iperf3 Integration
- ✅ Active throughput testing alongside WiFi monitoring
- ✅ Upload testing (client → server)
- ✅ Download testing (server → client) with `-R` flag
- ✅ Parallel streams support (`-P N`)
- ✅ UDP mode support (`-u`)
- ✅ Automatic start/stop with sessions
- ✅ Configuration stored in database

### Analysis & Export
- ✅ Session statistics (min/avg/max for all metrics)
- ✅ Multi-session comparison
- ✅ CSV export for Excel/Python/R
- ✅ InfluxDB line protocol export for Grafana
- ✅ Time-series data ready for plotting

### Configuration
- ✅ .env file support for defaults
- ✅ Configurable sample interval
- ✅ Configurable test duration
- ✅ Default iperf3 server/port/streams
- ✅ Custom database and export paths

### CLI Interface
- ✅ Intuitive command structure
- ✅ Comprehensive help messages with examples
- ✅ Short flags for common options (-l, -a, -d, -P, -R, -u)
- ✅ Grouped argument display (iperf3 options separate)

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `start` | Start monitoring session | `start -l "Kitchen" -a "R770" -d 5` |
| `stop` | Stop active session | `stop` or `stop 2` |
| `list` | List all sessions | `list` or `list --limit 50` |
| `stats` | Show session statistics | `stats 1` |
| `export` | Export to CSV | `export 1` or `export 1 -o custom.csv` |
| `influx` | Export to InfluxDB | `influx 1` or `influx 1 --version 1.x` |
| `compare` | Compare sessions | `compare 1 2 3` |

## Use Cases

### 1. Rate@Range Testing
Compare WiFi performance at different distances:
```bash
# Test at 20ft, 40ft, 60ft from AP
wifi_listener.py start -l "20ft" -a "R770" -d 5
wifi_listener.py start -l "40ft" -a "R770" -d 5
wifi_listener.py start -l "60ft" -a "R770" -d 5

# Compare results
wifi_listener.py compare 1 2 3
```

### 2. AP Comparison
Compare two access points at same location:
```bash
# Test AP1
wifi_listener.py start -l "Kitchen" -a "AP1" -d 5

# Test AP2
wifi_listener.py start -l "Kitchen" -a "AP2" -d 5

# Compare
wifi_listener.py stats 1
wifi_listener.py stats 2
```

### 3. Active vs Passive Testing
See difference between link capability and actual throughput:
```bash
# Passive (link capability)
wifi_listener.py start -l "Office" -a "R770" -d 3

# Active upload (sustained throughput)
wifi_listener.py start -l "Office" -a "R770" -d 5 \
  --iperf3-server 192.168.1.100 -P 4

# Active download
wifi_listener.py start -l "Office" -a "R770" -d 5 \
  --iperf3-server 192.168.1.100 -P 4 -R
```

### 4. Time-Series Analysis
Export for visualization:
```bash
# Export to CSV for plotting
wifi_listener.py export 1

# Export to InfluxDB for Grafana
wifi_listener.py influx 1
```

## Metrics Collected

| Metric | Unit | Description |
|--------|------|-------------|
| Signal (RSSI) | dBm | Received signal strength |
| Noise Floor | dBm | Background RF noise |
| SNR | dB | Signal-to-noise ratio (calculated) |
| TX Rate | Mbps | Transmission rate (upload) |
| Channel | - | WiFi channel number |
| Channel Width | MHz | 20/40/80/160 |
| Frequency Band | - | 2GHz or 5GHz |
| PHY Mode | - | 802.11 standard (ax/ac/n/etc) |
| MCS Index | - | Modulation & coding scheme |
| Security | - | WPA2/WPA3/etc |
| Timestamp | ISO | Exact time of measurement |

## Platform Support

- ✅ **macOS** (uses `system_profiler SPAirPortDataType`)
- ❌ Linux (would need different collection method)
- ❌ Windows (would need different collection method)

## Dependencies

**None!** 🎉

Uses only Python standard library:
- `sqlite3` - Database
- `subprocess` - Run system commands
- `argparse` - CLI parsing
- `csv` - CSV export
- `datetime` - Timestamps
- `re` - Parsing
- `threading` - Background iperf3

Optional:
- `iperf3` - For active throughput testing (install via `brew install iperf3`)

## Documentation

- `README.md` - Main documentation
- `IPERF3_QUICKSTART.md` - iperf3 setup guide
- `IPERF3_INTEGRATION.md` - Technical iperf3 details
- `GRAFANA_SETUP.md` - Grafana visualization guide
- `ENV_SETUP.md` - Environment configuration
- `GITHUB_SETUP.md` - GitHub publishing
- `CHANGELOG.md` - Version history
- `FEATURES.md` - This file

## Future Enhancements

Potential features for advanced fork:
- Real-time InfluxDB streaming (no export step)
- RX rate capture via CoreWLAN framework
- Monitor mode for ambient WiFi analysis
- Packet capture integration
- GUI/web interface
- Linux/Windows support
- Automated testing scripts
- Report generation
