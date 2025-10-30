"""
WiFi data collector using macOS system_profiler
"""

import subprocess
import re
from datetime import datetime
from typing import Optional, Dict, Any


class SystemProfilerCollector:
    """
    Collects WiFi metrics using macOS system_profiler SPAirPortDataType
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the collector

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout

    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect current WiFi metrics

        Returns:
            dict: WiFi metrics or None if not connected/error
        """
        raw_output = self._run_system_profiler()
        if not raw_output:
            return None

        return self._parse_current_network(raw_output)

    def _run_system_profiler(self) -> Optional[str]:
        """
        Execute system_profiler command

        Returns:
            str: Command output or None on error
        """
        try:
            result = subprocess.run(
                ["system_profiler", "SPAirPortDataType"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            print(f"WARNING: system_profiler timed out after {self.timeout}s")
            return None
        except FileNotFoundError:
            print("ERROR: system_profiler not found")
            return None
        except Exception as e:
            print(f"ERROR running system_profiler: {e}")
            return None

    def _parse_current_network(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse system_profiler output to extract current network metrics

        Args:
            output: Raw system_profiler output

        Returns:
            dict: Parsed metrics or None if not connected
        """
        if not output:
            return None

        # Find the "Current Network Information:" section
        current_net_match = re.search(
            r'Current Network Information:\s*\n\s+([^:]+):\s*\n((?:\s+[^\n]+\n)+)',
            output,
            re.DOTALL
        )

        if not current_net_match:
            return None  # Not connected to WiFi

        ssid = current_net_match.group(1).strip()
        network_section = current_net_match.group(2)

        # Parse metrics using regex patterns
        patterns = {
            'phy_mode': r'PHY Mode:\s*([^\n]+)',
            'channel': r'Channel:\s*(\d+)',
            'frequency_band': r'Channel:\s*\d+\s*\(([^,]+)',  # 2GHz or 5GHz
            'channel_width_mhz': r'Channel:\s*\d+\s*\([^,]+,\s*(\d+)MHz\)',
            'country_code': r'Country Code:\s*([^\n]+)',
            'network_type': r'Network Type:\s*([^\n]+)',
            'security': r'Security:\s*([^\n]+)',
            'signal_dbm': r'Signal / Noise:\s*(-?\d+)\s*dBm',
            'noise_dbm': r'Signal / Noise:\s*-?\d+\s*dBm\s*/\s*(-?\d+)\s*dBm',
            'tx_rate_mbps': r'Transmit Rate:\s*(\d+)',
            'mcs_index': r'MCS Index:\s*(\d+)',
            'bssid': r'BSSID:\s*([^\n]+)',  # MAC address of AP
        }

        data = {
            'ssid': ssid,
            'timestamp': datetime.now().isoformat()
        }

        # Extract all available metrics
        for key, pattern in patterns.items():
            match = re.search(pattern, network_section)
            if match:
                value = match.group(1).strip()

                # Convert numeric fields to integers
                if key in ['channel', 'channel_width_mhz', 'signal_dbm',
                          'noise_dbm', 'tx_rate_mbps', 'mcs_index']:
                    try:
                        data[key] = int(value)
                    except ValueError:
                        data[key] = value
                else:
                    data[key] = value

        # Calculate SNR (Signal-to-Noise Ratio)
        if 'signal_dbm' in data and 'noise_dbm' in data:
            try:
                data['snr_db'] = data['signal_dbm'] - data['noise_dbm']
            except (TypeError, ValueError):
                pass

        return data

    def is_connected(self) -> bool:
        """
        Check if currently connected to WiFi

        Returns:
            bool: True if connected
        """
        data = self.collect()
        return data is not None and 'ssid' in data
