#!/usr/bin/env python3
"""
Test script to explore what data we can capture using system_profiler.
This is the modern replacement for the deprecated airport utility.
"""

import subprocess
import re
import pprint
from datetime import datetime

def run_system_profiler():
    """Get detailed WiFi info using system_profiler"""
    try:
        result = subprocess.run(
            ["system_profiler", "SPAirPortDataType"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def parse_current_network(output):
    """
    Parse system_profiler output to extract current network metrics.
    This is optimized for rate@range testing.
    """
    if not output:
        return None

    data = {
        'timestamp': datetime.now().isoformat(),
        'connected': False
    }

    # Find the "Current Network Information:" section
    # Look for the pattern with proper indentation
    current_net_match = re.search(
        r'Current Network Information:\s*\n\s+([^:]+):\s*\n((?:\s+[^\n]+\n)+)',
        output,
        re.DOTALL
    )

    if not current_net_match:
        return data

    data['connected'] = True
    data['ssid'] = current_net_match.group(1).strip()

    # Extract all the metrics from the current network section
    network_section = current_net_match.group(2)

    # Parse key-value pairs
    patterns = {
        'phy_mode': r'PHY Mode:\s*([^\n]+)',
        'channel': r'Channel:\s*(\d+)',
        'frequency': r'Channel:\s*\d+\s*\(([^,]+)',  # 2GHz or 5GHz
        'channel_width': r'Channel:\s*\d+\s*\([^,]+,\s*(\d+)MHz\)',
        'country_code': r'Country Code:\s*([^\n]+)',
        'network_type': r'Network Type:\s*([^\n]+)',
        'security': r'Security:\s*([^\n]+)',
        'signal': r'Signal / Noise:\s*(-?\d+)\s*dBm',
        'noise': r'Signal / Noise:\s*-?\d+\s*dBm\s*/\s*(-?\d+)\s*dBm',
        'tx_rate': r'Transmit Rate:\s*(\d+)',
        'mcs_index': r'MCS Index:\s*(\d+)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, network_section)
        if match:
            data[key] = match.group(1).strip()

    # Calculate SNR (Signal-to-Noise Ratio)
    if 'signal' in data and 'noise' in data:
        try:
            data['snr'] = int(data['signal']) - int(data['noise'])
        except:
            pass

    return data

def parse_nearby_networks(output):
    """Extract information about nearby networks"""
    if not output:
        return []

    networks = []

    # Find "Other Local Wi-Fi Networks:" section
    other_nets_match = re.search(
        r'Other Local Wi-Fi Networks:(.*?)(?=\n\s{2}[a-zA-Z]|\Z)',
        output,
        re.DOTALL
    )

    if not other_nets_match:
        return networks

    section = other_nets_match.group(1)

    # Parse each network
    network_blocks = re.findall(
        r'\s+([^:]+):\s*\n((?:\s{12,}[^\n]+\n)+)',
        section
    )

    for ssid, details in network_blocks:
        net = {'ssid': ssid.strip()}

        # Extract details
        patterns = {
            'phy_mode': r'PHY Mode:\s*([^\n]+)',
            'channel': r'Channel:\s*(\d+)',
            'frequency': r'Channel:\s*\d+\s*\(([^,]+)',
            'channel_width': r'Channel:\s*\d+\s*\([^,]+,\s*(\d+)MHz\)',
            'security': r'Security:\s*([^\n]+)',
            'signal': r'Signal / Noise:\s*(-?\d+)\s*dBm',
            'noise': r'Signal / Noise:\s*-?\d+\s*dBm\s*/\s*(-?\d+)\s*dBm',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, details)
            if match:
                net[key] = match.group(1).strip()

        # Calculate SNR
        if 'signal' in net and 'noise' in net:
            try:
                net['snr'] = int(net['signal']) - int(net['noise'])
            except:
                pass

        networks.append(net)

    return networks

def main():
    print("=" * 80)
    print("macOS WiFi Data Capture Test (system_profiler)")
    print("=" * 80)
    print()

    print("Gathering WiFi data...")
    raw_output = run_system_profiler()

    if not raw_output:
        print("ERROR: Failed to get system_profiler data")
        return

    # Parse current connection
    print("\n" + "=" * 80)
    print("CURRENT CONNECTION METRICS (for rate@range testing)")
    print("=" * 80)

    current = parse_current_network(raw_output)

    if current and current['connected']:
        print(f"\nConnected to: {current['ssid']}")
        print(f"Timestamp: {current['timestamp']}")
        print()
        print("Key Metrics:")
        print("-" * 40)

        # Display in a nice format
        metrics = [
            ('SSID', 'ssid'),
            ('Signal (RSSI)', 'signal', 'dBm'),
            ('Noise Floor', 'noise', 'dBm'),
            ('SNR', 'snr', 'dB'),
            ('TX Rate', 'tx_rate', 'Mbps'),
            ('MCS Index', 'mcs_index'),
            ('Channel', 'channel'),
            ('Channel Width', 'channel_width', 'MHz'),
            ('Frequency Band', 'frequency'),
            ('PHY Mode', 'phy_mode'),
            ('Security', 'security'),
        ]

        for item in metrics:
            label = item[0]
            key = item[1]
            unit = item[2] if len(item) > 2 else ''

            if key in current:
                value = current[key]
                if unit:
                    print(f"  {label:20s}: {value} {unit}")
                else:
                    print(f"  {label:20s}: {value}")

        print()
        print("Full data structure:")
        print("-" * 40)
        pprint.pprint(current, width=80)

    else:
        print("\nNot connected to WiFi")

    # Parse nearby networks
    print("\n" + "=" * 80)
    print("NEARBY NETWORKS")
    print("=" * 80)

    nearby = parse_nearby_networks(raw_output)
    print(f"\nFound {len(nearby)} nearby networks")

    if nearby:
        # Sort by signal strength
        nearby.sort(key=lambda x: int(x.get('signal', -100)), reverse=True)

        print("\nTop 10 by signal strength:")
        print("-" * 80)
        print(f"{'SSID':25s} {'Signal':>8s} {'Noise':>8s} {'SNR':>6s} {'Ch':>4s} {'Width':>6s} {'Freq':>5s} {'PHY Mode':15s}")
        print("-" * 80)

        for net in nearby[:10]:
            ssid = net.get('ssid', 'N/A')[:24]
            signal = net.get('signal', 'N/A')
            noise = net.get('noise', 'N/A')
            snr = str(net.get('snr', 'N/A'))
            channel = net.get('channel', 'N/A')
            width = net.get('channel_width', 'N/A')
            freq = net.get('frequency', 'N/A')
            phy = net.get('phy_mode', 'N/A')[:14]

            print(f"{ssid:25s} {signal:>8s} {noise:>8s} {snr:>6s} {channel:>4s} {width:>6s} {freq:>5s} {phy:15s}")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("\nSummary:")
    print(f"  - Connected: {'Yes' if current and current['connected'] else 'No'}")
    if current and current['connected']:
        print(f"  - Current SSID: {current['ssid']}")
        print(f"  - Signal: {current.get('signal', 'N/A')} dBm")
        print(f"  - TX Rate: {current.get('tx_rate', 'N/A')} Mbps")
    print(f"  - Nearby networks: {len(nearby)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
