"""
WiFi data collector using macOS wdutil (requires sudo)

wdutil provides more detailed WiFi information than system_profiler,
including BSSID, CCA (channel utilization), Guard Interval, and NSS.

Falls back to system_profiler if sudo access is not available.
"""

import subprocess
import re
from datetime import datetime
from typing import Optional, Dict, Any


class WDUtilCollector:
    """
    Collects WiFi metrics using macOS wdutil (with sudo fallback to system_profiler)
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the collector

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout
        self.use_wdutil = self._check_wdutil_access()

    def _check_wdutil_access(self) -> bool:
        """
        Check if wdutil is accessible without password

        Returns:
            bool: True if sudo wdutil works without password
        """
        try:
            result = subprocess.run(
                ['sudo', '-n', 'wdutil', 'info'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False

    def collect(self) -> Optional[Dict[str, Any]]:
        """
        Collect current WiFi metrics

        Merges wdutil data (CCA, NSS, Guard Interval, BSSID when available)
        with system_profiler data (reliable SSID, all other metrics).

        Returns:
            dict: WiFi metrics or None if not connected/error
        """
        # Always get system_profiler data as baseline
        from collectors.system_profiler import SystemProfilerCollector
        sp_collector = SystemProfilerCollector(timeout=self.timeout)
        data = sp_collector.collect()

        if not data:
            return None

        # If wdutil is available, augment with additional metrics
        if self.use_wdutil:
            raw_output = self._run_wdutil()
            if raw_output:
                wdutil_data = self._parse_wdutil(raw_output)
                if wdutil_data:
                    # Merge wdutil-specific fields into system_profiler data
                    # Only add fields that wdutil provides uniquely
                    if 'cca_percent' in wdutil_data:
                        data['cca_percent'] = wdutil_data['cca_percent']
                    if 'nss' in wdutil_data:
                        data['nss'] = wdutil_data['nss']
                    if 'guard_interval' in wdutil_data:
                        data['guard_interval'] = wdutil_data['guard_interval']
                    # Use wdutil BSSID if available and not redacted
                    if 'bssid' in wdutil_data and wdutil_data['bssid'] != '<redacted>':
                        data['bssid'] = wdutil_data['bssid']

        return data

    def _run_wdutil(self) -> Optional[str]:
        """
        Execute wdutil command

        Returns:
            str: Command output or None on error
        """
        try:
            result = subprocess.run(
                ['sudo', '-n', 'wdutil', 'info'],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except subprocess.TimeoutExpired:
            print(f"WARNING: wdutil timed out after {self.timeout}s")
            return None
        except Exception as e:
            print(f"ERROR running wdutil: {e}")
            return None

    def _parse_wdutil(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse wdutil output to extract WiFi metrics

        Args:
            output: Raw wdutil output

        Returns:
            dict: Parsed metrics or None if not connected
        """
        if not output or 'WIFI' not in output:
            return None

        # Extract WiFi section
        wifi_match = re.search(
            r'WIFI\s*\n[-—]+\s*\n(.*?)(?=\n[-—]+|$)',
            output,
            re.DOTALL
        )

        if not wifi_match:
            return None

        wifi_section = wifi_match.group(1)

        # Parse metrics using regex patterns
        patterns = {
            'ssid': r'SSID\s*:\s*([^\n]+)',
            'bssid': r'BSSID\s*:\s*([a-fA-F0-9:]+)',
            'signal_dbm': r'RSSI\s*:\s*(-?\d+)\s*dBm',
            'noise_dbm': r'Noise\s*:\s*(-?\d+)\s*dBm',
            'tx_rate_mbps': r'Tx Rate\s*:\s*([\d.]+)\s*Mbps',
            'channel': r'Channel\s*:\s*\d+g(\d+)/',  # Extract channel number from "5g149/80"
            'channel_width_mhz': r'Channel\s*:\s*\d+g\d+/(\d+)',  # Extract width from "5g149/80"
            'frequency_band': r'Channel\s*:\s*(\d+)g',  # Extract band (2 or 5)
            'phy_mode': r'PHY Mode\s*:\s*([^\n]+)',
            'mcs_index': r'MCS Index\s*:\s*(\d+)',
            'security': r'Security\s*:\s*([^\n]+)',
            'country_code': r'Country Code\s*:\s*([^\n]+)',
            'cca_percent': r'CCA\s*:\s*(\d+)\s*%',  # Channel Clear Assessment
            'guard_interval': r'Guard Interval\s*:\s*(\d+)',  # 800ns or 3200ns
            'nss': r'NSS\s*:\s*(\d+)',  # Number of Spatial Streams
        }

        data = {
            'timestamp': datetime.now().isoformat()
        }

        # Extract all available metrics
        for key, pattern in patterns.items():
            match = re.search(pattern, wifi_section)
            if match:
                value = match.group(1).strip()

                # Convert numeric fields to appropriate types
                if key in ['channel', 'channel_width_mhz', 'signal_dbm',
                          'noise_dbm', 'mcs_index', 'cca_percent', 'guard_interval', 'nss']:
                    try:
                        data[key] = int(value)
                    except ValueError:
                        data[key] = value
                elif key == 'tx_rate_mbps':
                    try:
                        data[key] = int(float(value))
                    except ValueError:
                        data[key] = value
                elif key == 'frequency_band':
                    # Convert "2" to "2GHz", "5" to "5GHz"
                    data['frequency_band'] = f"{value} GHz"
                elif key == 'phy_mode':
                    # Convert "11ax" to "802.11ax"
                    if value.startswith('11'):
                        data[key] = f"802.{value}"
                    else:
                        data[key] = value
                else:
                    data[key] = value

        # Calculate SNR (Signal-to-Noise Ratio)
        if 'signal_dbm' in data and 'noise_dbm' in data:
            try:
                data['snr_db'] = data['signal_dbm'] - data['noise_dbm']
            except (TypeError, ValueError):
                pass

        # Must have at least SSID to be valid
        if 'ssid' not in data:
            return None

        return data

    def is_connected(self) -> bool:
        """
        Check if currently connected to WiFi

        Returns:
            bool: True if connected
        """
        data = self.collect()
        return data is not None and 'ssid' in data
