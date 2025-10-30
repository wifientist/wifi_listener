# iperf3 Integration Summary

## Key iperf3 Parameters for WiFi Testing

### Essential Flags:
- `-c SERVER_IP` - Connect to iperf3 server (required)
- `-p PORT` - Server port (default: 5201)
- `-t DURATION` - Test duration in seconds
- `-i 4` - Report interval (matches WiFi sample interval)

### Performance Flags:
- `-P N` - Parallel streams (default: 1)
  - **Recommended: `-P 4`** for WiFi testing to saturate the link
  - More streams = better utilization of available bandwidth
  - Typical: 1-8 streams depending on your needs

- `-R` - Reverse mode (server sends to client)
  - **Without `-R`**: Tests upload (client → server) - matches TX rate
  - **With `-R`**: Tests download (server → client) - tests RX performance
  - **Recommendation**: Run both for complete picture

- `-u` - UDP mode instead of TCP
  - TCP (default): Real-world performance with congestion control
  - UDP: Raw throughput, good for latency testing
  - **Recommendation**: Use TCP for rate@range testing

## Database Schema Added

The sessions table now includes:
```sql
iperf3_enabled BOOLEAN
iperf3_server TEXT
iperf3_port INTEGER
iperf3_parallel INTEGER
iperf3_reverse BOOLEAN
iperf3_udp BOOLEAN
```

## Typical Usage Scenarios

### Scenario 1: Upload Testing (matches TX Rate)
```bash
python3 wifi_listener.py start \
  --location "Kitchen - 20ft" \
  --ap-name "R770" \
  --duration 5 \
  --iperf3-server 192.168.1.100 \
  --iperf3-parallel 4
```

### Scenario 2: Download Testing (RX performance)
```bash
python3 wifi_listener.py start \
  --location "Kitchen - 20ft" \
  --ap-name "R770" \
  --duration 5 \
  --iperf3-server 192.168.1.100 \
  --iperf3-parallel 4 \
  --iperf3-reverse
```

### Scenario 3: Without iperf3 (idle monitoring)
```bash
python3 wifi_listener.py start \
  --location "Kitchen - 20ft" \
  --ap-name "R770" \
  --duration 5
# No iperf3 flags = passive monitoring only
```

## iperf3 Server Setup

On another machine on your LAN:
```bash
# Install
brew install iperf3  # macOS
# or
sudo apt install iperf3  # Linux

# Run server
iperf3 -s

# Run on specific port
iperf3 -s -p 5201
```

## What Happens During Testing

1. WiFi Listener starts monitoring
2. iperf3 test launches in background thread
3. Both run simultaneously for the duration
4. WiFi metrics captured every 4 seconds
5. iperf3 shows final throughput summary
6. Session marked with iperf3 parameters in database

## Viewing Results

When you list sessions or view stats, you'll see if iperf3 was enabled:
```
ID  Location            AP    iperf3  Samples  Avg Signal  Avg TX Rate
1   Kitchen-20ft       R770   No      75       -45 dBm     1200 Mbps
2   Kitchen-20ft       R770   Yes(4P) 75       -45 dBm     950 Mbps
```

The second test shows actual sustained throughput with load!

## Recommended Testing Matrix

For each location, run:
1. **Idle** - No iperf3
2. **Upload** - iperf3 with `-P 4`
3. **Download** - iperf3 with `-P 4 -R`

This gives you:
- Link capability (idle)
- Actual upload performance (upload)
- Actual download performance (download)

## Implementation Status

- [x] Database schema updated
- [x] IPerf3Runner module created
- [ ] CLI integration (in progress)
- [ ] Session start/stop with iperf3
- [ ] Display iperf3 status in list/stats commands

## Next Steps

Completing the integration into wifi_listener.py main CLI.
