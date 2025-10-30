#!/usr/bin/env python3
"""
Test script to explore what data we can capture from macOS airport utility.
This will show all available WiFi metrics for connected networks.
"""

import subprocess
import json
import pprint
from datetime import datetime

# Path to the airport utility on macOS
AIRPORT_PATH = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"

def run_airport_info():
    """Get detailed info about current WiFi connection using airport -I"""
    try:
        result = subprocess.run(
            [AIRPORT_PATH, "-I"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print("ERROR: airport command timed out")
        return None
    except FileNotFoundError:
        print(f"ERROR: airport utility not found at {AIRPORT_PATH}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def parse_airport_output(output):
    """Parse the airport -I output into a dictionary"""
    if not output or not output.strip():
        return {"connected": False, "error": "Not connected to WiFi"}

    data = {}
    for line in output.strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()

    # Add timestamp
    data['timestamp'] = datetime.now().isoformat()
    data['connected'] = True

    return data

def run_airport_scan():
    """Scan for nearby networks using airport -s"""
    try:
        result = subprocess.run(
            [AIRPORT_PATH, "-s"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout
    except Exception as e:
        print(f"ERROR scanning: {e}")
        return None

def main():
    print("=" * 80)
    print("macOS Airport Utility WiFi Data Capture Test")
    print("=" * 80)
    print()

    # Test 1: Get current connection info
    print("TEST 1: Current Connection Info (airport -I)")
    print("-" * 80)
    raw_output = run_airport_info()

    if raw_output:
        print("Raw output:")
        print(raw_output)
        print()

        print("Parsed data:")
        parsed = parse_airport_output(raw_output)
        pprint.pprint(parsed, width=80)
        print()

        # Highlight key metrics for rate@range testing
        if parsed.get('connected'):
            print("KEY METRICS FOR RATE@RANGE TESTING:")
            print("-" * 80)
            important_fields = [
                'agrCtlRSSI',      # RSSI in dBm
                'agrCtlNoise',     # Noise floor in dBm
                'lastTxRate',      # Current TX rate in Mbps
                'maxRate',         # Max supported rate
                'channel',         # Current channel
                'MCS',             # MCS index
                'NSS',             # Number of spatial streams
                'PHY Mode',        # 802.11 mode (a/b/g/n/ac/ax)
                'BSSID',           # AP MAC address
                'SSID',            # Network name
            ]

            for field in important_fields:
                if field in parsed:
                    print(f"  {field:20s}: {parsed[field]}")
            print()
    else:
        print("Failed to get airport info - are you connected to WiFi?")
        print()

    # Test 2: Scan for nearby networks
    print("\nTEST 2: Nearby Networks Scan (airport -s)")
    print("-" * 80)
    print("Scanning for nearby networks (this may take a few seconds)...")
    scan_output = run_airport_scan()

    if scan_output:
        lines = scan_output.strip().split('\n')
        print(f"Found {len(lines)-1} networks:")
        print()
        # Show first 10 lines (header + 9 networks)
        for line in lines[:10]:
            print(line)
        if len(lines) > 10:
            print(f"... and {len(lines)-10} more")
    else:
        print("Failed to scan networks")

    print()
    print("=" * 80)
    print("Test complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
