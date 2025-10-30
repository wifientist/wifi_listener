# InfluxDB + Grafana Setup Guide

Complete guide for visualizing WiFi metrics in Grafana with time-series charts.

## Quick Start

### 1. Export Data to InfluxDB Format

```bash
# Export a single session
python3 wifi_listener.py influx 1

# This creates session_1_influx.txt with InfluxDB line protocol
```

### 2. Setup InfluxDB (Docker - Easiest Method)

**InfluxDB 2.x (Recommended):**

```bash
# Start InfluxDB container
docker run -d -p 8086:8086 \
  --name influxdb \
  -v influxdb-data:/var/lib/influxdb2 \
  influxdb:2.7

# Open http://localhost:8086 and complete setup:
# - Username: admin
# - Password: <your-password>
# - Organization: wifi_testing
# - Bucket: wifi_metrics
# - Save your API token!
```

### 3. Import Data into InfluxDB

```bash
# Using the influx CLI
influx write \
  --bucket wifi_metrics \
  --org wifi_testing \
  --token YOUR_TOKEN_HERE \
  --file session_1_influx.txt

# Or using curl
curl -XPOST "http://localhost:8086/api/v2/write?org=wifi_testing&bucket=wifi_metrics" \
  --header "Authorization: Token YOUR_TOKEN_HERE" \
  --data-binary @session_1_influx.txt
```

### 4. Setup Grafana (Docker)

```bash
# Start Grafana container
docker run -d -p 3000:3000 \
  --name grafana \
  -v grafana-data:/var/lib/grafana \
  grafana/grafana:latest

# Open http://localhost:3000
# Default login: admin / admin (you'll be prompted to change)
```

### 5. Configure Grafana Data Source

1. Go to **Configuration** → **Data Sources** → **Add data source**
2. Select **InfluxDB**
3. Configure:
   - **Query Language**: Flux
   - **URL**: `http://host.docker.internal:8086` (Mac/Windows) or `http://172.17.0.1:8086` (Linux)
   - **Organization**: `wifi_testing`
   - **Token**: Your InfluxDB API token
   - **Default Bucket**: `wifi_metrics`
4. Click **Save & Test**

## Creating Dashboards

### Example Flux Queries for Grafana Panels

**Signal Strength Over Time:**
```flux
from(bucket: "wifi_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "wifi_metrics")
  |> filter(fn: (r) => r["_field"] == "signal")
  |> filter(fn: (r) => r["session_id"] == "1")
```

**TX Rate Over Time:**
```flux
from(bucket: "wifi_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "wifi_metrics")
  |> filter(fn: (r) => r["_field"] == "tx_rate")
  |> filter(fn: (r) => r["session_id"] == "1")
```

**SNR Over Time:**
```flux
from(bucket: "wifi_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "wifi_metrics")
  |> filter(fn: (r) => r["_field"] == "snr")
  |> filter(fn: (r) => r["session_id"] == "1")
```

**Compare Multiple Sessions (e.g., different APs):**
```flux
from(bucket: "wifi_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "wifi_metrics")
  |> filter(fn: (r) => r["_field"] == "tx_rate")
  |> filter(fn: (r) => r["session_id"] == "1" or r["session_id"] == "2")
  |> group(columns: ["ap_name", "session_id"])
```

**Compare by Location:**
```flux
from(bucket: "wifi_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "wifi_metrics")
  |> filter(fn: (r) => r["_field"] == "signal")
  |> group(columns: ["location"])
```

## Suggested Dashboard Panels

### Panel 1: Signal Metrics (Multi-axis)
- **Type**: Time series graph
- **Metrics**: Signal, Noise, SNR
- **Y-Axis**: dBm / dB
- **Legend**: Show values (min, avg, max)

### Panel 2: TX Rate
- **Type**: Time series graph
- **Metric**: tx_rate
- **Y-Axis**: Mbps
- **Alert**: Threshold when rate drops below certain value

### Panel 3: Channel Info
- **Type**: Time series graph
- **Metrics**: Channel, Channel Width, MCS Index
- **Display**: Step line (these change discretely)

### Panel 4: Stats Table
- **Type**: Stat panel
- **Show**: Current values for Signal, SNR, TX Rate
- **Thresholds**: Green (good), Yellow (fair), Red (poor)

### Panel 5: Session Comparison (Bar Chart)
- **Type**: Bar gauge or Bar chart
- **Metric**: Average TX Rate by session/location
- **Useful for**: Quick comparison across test runs

## Data Tags Available for Filtering

All your data includes these tags for filtering/grouping:
- `ssid` - Network name
- `phy_mode` - WiFi standard (802.11ax, ac, etc.)
- `band` - Frequency band (2GHz, 5GHz)
- `location` - Your test location
- `ap_name` - Your AP label
- `session_id` - Unique session identifier

## Workflow: Full Testing Cycle

```bash
# 1. Run tests at different locations
python3 wifi_listener.py start --location "20ft" --ap-name "AP1" --duration 5
python3 wifi_listener.py start --location "40ft" --ap-name "AP1" --duration 5
python3 wifi_listener.py start --location "60ft" --ap-name "AP1" --duration 5

# 2. Export all sessions to InfluxDB format
python3 wifi_listener.py influx 1
python3 wifi_listener.py influx 2
python3 wifi_listener.py influx 3

# 3. Import to InfluxDB
for file in session_*_influx.txt; do
  influx write --bucket wifi_metrics --org wifi_testing --token YOUR_TOKEN --file $file
done

# 4. View in Grafana
# Open http://localhost:3000 and create dashboard with time-series panels
```

## Alternative: InfluxDB 1.x

If you prefer InfluxDB 1.x:

```bash
# Export with 1.x flag
python3 wifi_listener.py influx 1 --version 1.x

# Docker setup
docker run -d -p 8086:8086 \
  --name influxdb \
  -v influxdb-data:/var/lib/influxdb \
  influxdb:1.8

# Create database
curl -XPOST http://localhost:8086/query --data-urlencode "q=CREATE DATABASE wifi_metrics"

# Import data
curl -XPOST 'http://localhost:8086/write?db=wifi_metrics' \
  --data-binary @session_1_influx.txt

# Grafana setup: Use InfluxQL instead of Flux
```

## Troubleshooting

**Connection refused from Grafana to InfluxDB:**
- Mac/Windows: Use `http://host.docker.internal:8086`
- Linux: Use `http://172.17.0.1:8086`
- Or: Run both containers on same Docker network

**No data showing in Grafana:**
- Check time range (your test data has specific timestamps)
- Verify bucket/database name matches
- Test Flux query in InfluxDB UI first

**Import fails:**
- Check your API token has write permissions
- Verify bucket/org names are correct
- Check InfluxDB logs: `docker logs influxdb`

## Tips

1. **Use variables** in Grafana for session_id, location, ap_name to easily switch views
2. **Set up annotations** to mark when you moved locations
3. **Create alerts** for signal quality thresholds
4. **Export dashboards** as JSON for reuse across different test setups
5. **Use transformation plugins** in Grafana to calculate additional metrics (e.g., packet loss correlation)
