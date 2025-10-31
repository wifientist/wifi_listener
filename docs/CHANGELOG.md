# Changelog

## [Unreleased] - iperf3 Integration

### Added
- **iperf3 Integration** for active throughput testing
  - Background iperf3 execution during WiFi monitoring
  - Support for upload testing (client → server)
  - Support for download testing (server → client) with `-R` flag
  - Parallel streams support with `-P` flag (recommended: 4)
  - UDP mode support with `-u` flag
  - Automatic start/stop with monitoring sessions

- **CLI Arguments**
  - `--iperf3-server IP` - Enable iperf3 and specify server
  - `--iperf3-port PORT` - Server port (default: 5201)
  - `-P N` or `--iperf3-parallel N` - Number of parallel streams
  - `-R` or `--iperf3-reverse` - Reverse mode (download test)
  - `-u` or `--iperf3-udp` - Use UDP instead of TCP

- **Database Schema**
  - Added iperf3 configuration fields to sessions table
  - Track iperf3_enabled, server, port, parallel, reverse, udp flags

- **UI Updates**
  - List command shows iperf3 status (e.g., "Yes(P4)/R")
  - Stats command displays iperf3 configuration
  - Session start shows iperf3 test parameters

- **Documentation**
  - IPERF3_QUICKSTART.md - Quick start guide
  - IPERF3_INTEGRATION.md - Technical integration details
  - Updated README with iperf3 examples

### Changed
- Session creation now accepts iperf3 parameters
- Monitoring loop starts/stops iperf3 alongside WiFi collection

## [1.0.0] - Initial Release

### Added
- WiFi metrics collection using macOS `system_profiler`
- SQLite database storage with session management
- Real-time monitoring display (Signal, Noise, SNR, TX Rate, Channel)
- Session start/stop/list/stats commands
- CSV export for Excel/Python analysis
- InfluxDB line protocol export for Grafana
- Session comparison tool
- Auto-stop with duration parameter
- Graceful Ctrl+C handling
- Zero external dependencies (pure Python stdlib)

### Metrics Collected
- Signal (RSSI) in dBm
- Noise floor in dBm
- SNR (Signal-to-Noise Ratio) in dB
- TX Rate in Mbps
- Channel number
- Channel width (20/40/80/160 MHz)
- Frequency band (2GHz/5GHz)
- PHY mode (802.11ax/ac/n/etc)
- MCS index
- Security type
- Timestamp

### Documentation
- README.md - Main documentation
- GRAFANA_SETUP.md - InfluxDB + Grafana setup guide
- GITHUB_SETUP.md - GitHub publishing instructions
- LICENSE - MIT License
