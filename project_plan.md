# WiFi Listener - Rate@Range Testing Tool

## Project Overview
Monitor WiFi connection metrics at 4-5 second intervals for 3-5 minute test sessions at various locations. Collect data into SQLite database for later analysis and time-series visualization.

## Use Case
- Test multiple locations (different distances/positions from AP)
- Capture low/avg/high metrics for each KPI
- Generate time-series charts with shared time axis
- Compare performance between two WiFi access points

## Project Structure
```
wifi_listener/
├── wifi_listener.py          # Main entry point / CLI
├── config.py                  # Configuration settings
├── db/
│   ├── __init__.py
│   ├── schema.py              # Database schema/models
│   └── database.py            # Database operations
├── collectors/
│   ├── __init__.py
│   └── system_profiler.py     # WiFi data collection via system_profiler
├── data/
│   └── wifi_metrics.db        # SQLite database (created at runtime)
├── test_system_profiler.py    # Test script (existing)
└── requirements.txt           # Python dependencies
```

## Database Schema

### Table: sessions
Tracks each test session (e.g., "Kitchen - 20ft from AP1")
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,              -- e.g., "Kitchen", "Bedroom", "Garage"
    notes TEXT,                           -- Optional test notes
    ap_name TEXT,                         -- Which AP being tested
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    sample_interval_seconds REAL DEFAULT 4.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: wifi_samples
Individual WiFi metric readings
```sql
CREATE TABLE wifi_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Connection Info
    ssid TEXT NOT NULL,
    bssid TEXT,                          -- AP MAC address (if available)

    -- Signal Quality
    signal_dbm INTEGER,                  -- RSSI
    noise_dbm INTEGER,                   -- Noise floor
    snr_db INTEGER,                      -- Calculated SNR

    -- Performance Metrics
    tx_rate_mbps INTEGER,                -- Transmit rate (KEY metric!)

    -- Channel Info
    channel INTEGER,
    channel_width_mhz INTEGER,           -- 20, 40, 80, 160
    frequency_band TEXT,                 -- "2GHz" or "5GHz"

    -- Protocol Info
    phy_mode TEXT,                       -- "802.11ax", "802.11ac", etc.
    mcs_index INTEGER,                   -- MCS index

    -- Additional
    security TEXT,
    country_code TEXT,

    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_samples_session ON wifi_samples(session_id);
CREATE INDEX idx_samples_timestamp ON wifi_samples(timestamp);
CREATE INDEX idx_sessions_start ON sessions(start_time);
```

## Key Metrics for Rate@Range Testing

1. **Signal (RSSI)** - Signal strength in dBm
2. **Noise** - Background noise in dBm
3. **SNR** - Signal-to-Noise Ratio in dB
4. **TX Rate** - Actual throughput in Mbps (PRIMARY METRIC)
5. **Channel Width** - 20/40/80/160 MHz
6. **MCS Index** - Modulation & Coding Scheme
7. **PHY Mode** - 802.11 standard (ac vs ax comparison)

## Workflow

1. Start a test session with location info
   ```bash
   python wifi_listener.py start --location "Kitchen - 20ft" --ap "AP1-butfirstcoffee"
   ```

2. Collector runs every 4 seconds, storing to database

3. Stop the session (or auto-stop after duration)
   ```bash
   python wifi_listener.py stop
   ```

4. Export/analyze data
   ```bash
   python wifi_listener.py export --session-id 1 --format csv
   python wifi_listener.py stats --session-id 1
   ```

## Sample Analysis Queries

```sql
-- Get min/avg/max for a session
SELECT
    MIN(signal_dbm) as min_signal,
    AVG(signal_dbm) as avg_signal,
    MAX(signal_dbm) as max_signal,
    MIN(tx_rate_mbps) as min_rate,
    AVG(tx_rate_mbps) as avg_rate,
    MAX(tx_rate_mbps) as max_rate,
    MIN(snr_db) as min_snr,
    AVG(snr_db) as avg_snr,
    MAX(snr_db) as max_snr
FROM wifi_samples
WHERE session_id = ?;

-- Time series data for plotting
SELECT
    timestamp,
    signal_dbm,
    tx_rate_mbps,
    snr_db,
    mcs_index
FROM wifi_samples
WHERE session_id = ?
ORDER BY timestamp;
```

## Implementation Phases

### Phase 1: Core Data Collection (NOW)
- [x] Test data collection with system_profiler
- [ ] Create database schema
- [ ] Implement WiFi collector module
- [ ] Build main sampling loop
- [ ] Create basic CLI for start/stop

### Phase 2: Session Management
- [ ] Session tracking (location, AP name, notes)
- [ ] Auto-stop after duration
- [ ] Session listing/viewing

### Phase 3: Analysis & Export
- [ ] Stats summary (min/avg/max per session)
- [ ] CSV export for plotting
- [ ] Basic visualization (optional)

## Notes
- System_profiler takes ~3.6s, so 4-5 second interval is realistic
- SQLite is perfect for this use case (lightweight, portable, good for time-series)
- Can run multiple sessions and compare later
