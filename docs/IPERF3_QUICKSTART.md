# iperf3 Quick Start Guide

## Setup iperf3 Server

On another machine on your LAN (can be Mac, Linux, Raspberry Pi, etc.):

```bash
# Install
brew install iperf3   # macOS
# or
sudo apt install iperf3   # Linux

# Run server
iperf3 -s

# Server is now listening on port 5201
```

## Usage Examples

### 1. Passive Monitoring (No iperf3)
```bash
python3 wifi_listener.py start \
  --location "Kitchen - 20ft" \
  --ap-name "R770" \
  --duration 5
```
**Shows:** Link capability, signal quality at idle

### 2. Upload Testing (Client → Server)
```bash
python3 wifi_listener.py start \
  --location "Kitchen - 20ft" \
  --ap-name "R770" \
  --duration 5 \
  --iperf3-server 192.168.1.100 \
  --iperf3-parallel 4
```
**Shows:** Actual sustained upload throughput under load
**Note:** Matches TX Rate metric (upload from your Mac)

### 3. Download Testing (Server → Client)
```bash
python3 wifi_listener.py start \
  --location "Kitchen - 20ft" \
  --ap-name "R770" \
  --duration 5 \
  --iperf3-server 192.168.1.100 \
  -P 4 \
  -R
```
**Shows:** Download performance (what you don't normally see in TX rate!)
**Note:** `-R` flag = reverse mode

## Key iperf3 Flags

- `--iperf3-server IP` - **Required** to enable iperf3
- `-P N` or `--iperf3-parallel N` - Number of parallel streams (recommended: 4)
- `-R` or `--iperf3-reverse` - Download test instead of upload
- `-u` or `--iperf3-udp` - Use UDP instead of TCP
- `--iperf3-port PORT` - Server port (default: 5201)

## Recommended Testing Matrix

For each location:
1. **Idle** - No iperf3 (shows link capability)
2. **Upload** - With `-P 4` (shows actual upload performance)
3. **Download** - With `-P 4 -R` (shows actual download performance)

This gives you complete picture of WiFi performance!

## What Happens

When you run with iperf3 enabled:
1. WiFi monitoring starts
2. iperf3 test launches in background
3. Both run simultaneously for the specified duration
4. WiFi metrics collected every 4 seconds
5. iperf3 shows throughput summary at end
6. All data stored in database with iperf3 flags

## Viewing iperf3 Sessions

```bash
# List shows iperf3 status
python3 wifi_listener.py list

# Example output:
# ID  Location          AP    iperf3      Samples
# 1   Kitchen-20ft     R770   No          75
# 2   Kitchen-20ft     R770   Yes(P4)     75
# 3   Kitchen-20ft     R770   Yes(P4)/R   75

# Stats shows iperf3 configuration
python3 wifi_listener.py stats 2
```

## Why Use Parallel Streams?

Single stream (`-P 1`) often can't saturate WiFi bandwidth due to TCP window size limits.
**Recommended: `-P 4`** for WiFi testing to get realistic maximum throughput.

## Troubleshooting

**"iperf3 not found"**
```bash
brew install iperf3
```

**"Could not connect to server"**
- Check server is running: `iperf3 -s`
- Check IP address is correct
- Check firewall allows port 5201
- Verify both devices on same network

**iperf3 fails but monitoring continues**
- This is expected behavior
- WiFi metrics still collected
- Session marked with iperf3 parameters for reference
