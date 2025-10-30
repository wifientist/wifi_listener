# WiFi Listener - Rate@Range Testing Tool

Monitor WiFi connection metrics and store them for analysis. Designed for comparing AP performance at different locations.

**macOS only** - Uses `system_profiler` to collect WiFi metrics.

## Features

- 📊 Collect WiFi metrics every 4 seconds (Signal, SNR, TX Rate, MCS, etc.)
- 💾 Store data in SQLite for analysis
- 📈 Export to CSV or InfluxDB for visualization
- 🔍 Compare multiple test sessions side-by-side
- 🎯 Perfect for rate@range testing between access points
- 🚀 Zero dependencies - pure Python stdlib

## Quick Start

### Start a test session
```bash
python3 wifi_listener.py start --location "Kitchen - 20ft" --ap-name "butfirstcoffee"
```

This will:
- Collect WiFi metrics every 4 seconds
- Display real-time readings
- Store everything in SQLite database
- Press Ctrl+C to stop

### Auto-stop after 5 minutes
```bash
python3 wifi_listener.py start --location "Bedroom - 40ft" --ap-name "AP1" --duration 5
```

### View all sessions
```bash
python3 wifi_listener.py list
```

### View session statistics
```bash
python3 wifi_listener.py stats 1
```

Shows min/avg/max for all metrics (Signal, Noise, SNR, TX Rate, MCS Index)

### Export session to CSV (for plotting)
```bash
python3 wifi_listener.py export 1
```

Creates a CSV file with time-series data ready for Excel, Python (matplotlib/pandas), or any plotting tool.

### Export to InfluxDB (for Grafana)
```bash
python3 wifi_listener.py influx 1
```

Creates InfluxDB line protocol file for import into InfluxDB. Perfect for Grafana dashboards with real-time visualization!

See [GRAFANA_SETUP.md](GRAFANA_SETUP.md) for complete InfluxDB + Grafana setup guide.

### Compare multiple sessions
```bash
python3 wifi_listener.py compare 1 2 3
```

Shows side-by-side comparison of metrics across sessions. Perfect for comparing:
- Same location, different APs
- Same AP, different locations
- Different test conditions

## Data Collected

Every sample includes:
- **Signal (RSSI)** - Signal strength in dBm
- **Noise Floor** - Background RF noise in dBm
- **SNR** - Signal-to-Noise Ratio in dB
- **TX Rate** - Transmission rate in Mbps (**PRIMARY METRIC**)
- **Channel** - WiFi channel number
- **Channel Width** - 20/40/80/160 MHz
- **Frequency Band** - 2GHz or 5GHz
- **PHY Mode** - 802.11 standard (ax/ac/n/etc)
- **MCS Index** - Modulation & Coding Scheme
- **Timestamp** - Exact time of reading

## Project Structure

```
wifi_listener/
├── wifi_listener.py       # Main CLI app
├── data/                   # SQLite database
│   └── wifi_metrics.db
├── exports/                # Exported CSV and InfluxDB files
│   ├── session_1_office.csv
│   └── session_1_influx.txt
├── db/                     # Database modules
├── collectors/             # Data collection modules
└── exporters/              # Export modules
```

SQLite database: `data/wifi_metrics.db`
Exports: `exports/` folder (CSV and InfluxDB line protocol files)

## Typical Workflow

1. **Test Location A** - Run 5 min session at 20ft from AP
2. **Test Location B** - Run 5 min session at 40ft from AP
3. **Test Location C** - Run 5 min session at 60ft from AP
4. **Compare** - Use stats command or export data for charts
5. **Repeat** - Test second AP and compare results

## Example Output

```
WiFi Monitoring Session Started
================================================================================
Session ID: 1
Location: Kitchen - 20ft
AP Name: butfirstcoffee
Connected to: butfirstcoffee
Sample Interval: 4.0 seconds
Duration: Manual stop (press Ctrl+C)
================================================================================

Collecting samples... (press Ctrl+C to stop)
Time                   Signal    Noise    SNR    TX Rate  Channel
--------------------------------------------------------------------------------
13:15:00                  -49      -90     41       1200      149
13:15:04                  -48      -90     42       1200      149
13:15:08                  -50      -89     39       1200      149
...
```

## Requirements

- macOS (uses `system_profiler` command)
- Python 3.6+
- No external dependencies (pure stdlib)

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/wifi_listener.git
cd wifi_listener
python3 wifi_listener.py --help
```

## Contributing

This is the **basic version** focused on simplicity and ease of use. For more advanced features (RX rate, monitor mode, packet capture), consider forking for a more complex implementation.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Roadmap / Ideas for Advanced Fork

- Real-time streaming to InfluxDB (no export step)
- RX rate capture using CoreWLAN framework
- Monitor mode for ambient WiFi analysis
- Packet capture integration
- Active throughput testing (iperf3 integration)
- GUI/web interface for real-time monitoring
