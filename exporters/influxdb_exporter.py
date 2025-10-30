"""
Export WiFi metrics to InfluxDB for Grafana visualization
"""

from datetime import datetime
from typing import List, Dict, Any


class InfluxDBExporter:
    """
    Export WiFi metrics to InfluxDB using line protocol format

    Supports both InfluxDB 1.x and 2.x
    """

    def __init__(self, measurement_name: str = "wifi_metrics"):
        """
        Initialize exporter

        Args:
            measurement_name: InfluxDB measurement name
        """
        self.measurement_name = measurement_name

    def format_line_protocol(self, samples: List[Dict[str, Any]],
                            session_info: Dict[str, Any] = None) -> List[str]:
        """
        Convert samples to InfluxDB line protocol format

        Args:
            samples: List of sample dictionaries from database
            session_info: Optional session metadata (location, ap_name, etc.)

        Returns:
            List of line protocol strings
        """
        lines = []

        for sample in samples:
            # Build tags (indexed fields for filtering/grouping)
            tags = []
            tags.append(f"ssid={self._escape_tag(sample.get('ssid', 'unknown'))}")

            if sample.get('bssid'):
                tags.append(f"bssid={self._escape_tag(sample['bssid'])}")

            if sample.get('phy_mode'):
                tags.append(f"phy_mode={self._escape_tag(sample['phy_mode'])}")

            if sample.get('frequency_band'):
                tags.append(f"band={self._escape_tag(sample['frequency_band'])}")

            # Add session metadata as tags if provided
            if session_info:
                if session_info.get('location'):
                    tags.append(f"location={self._escape_tag(session_info['location'])}")
                if session_info.get('ap_name'):
                    tags.append(f"ap_name={self._escape_tag(session_info['ap_name'])}")
                if session_info.get('id'):
                    tags.append(f"session_id={session_info['id']}")

            tags_str = ','.join(tags)

            # Build fields (actual metric values)
            fields = []

            # Numeric fields
            numeric_fields = [
                ('signal_dbm', 'signal'),
                ('noise_dbm', 'noise'),
                ('snr_db', 'snr'),
                ('tx_rate_mbps', 'tx_rate'),
                ('channel', 'channel'),
                ('channel_width_mhz', 'channel_width'),
                ('mcs_index', 'mcs'),
            ]

            for field_name, output_name in numeric_fields:
                if sample.get(field_name) is not None:
                    value = sample[field_name]
                    # Integer values should have 'i' suffix in InfluxDB
                    if isinstance(value, int):
                        fields.append(f"{output_name}={value}i")
                    else:
                        fields.append(f"{output_name}={value}")

            # String fields (quoted)
            if sample.get('security'):
                fields.append(f'security="{self._escape_field(sample["security"])}"')

            if not fields:
                continue  # Skip if no fields

            fields_str = ','.join(fields)

            # Parse timestamp
            timestamp = self._parse_timestamp(sample.get('timestamp'))
            timestamp_ns = int(timestamp.timestamp() * 1_000_000_000)

            # Build line: measurement,tags fields timestamp
            line = f"{self.measurement_name},{tags_str} {fields_str} {timestamp_ns}"
            lines.append(line)

        return lines

    def export_to_file(self, samples: List[Dict[str, Any]],
                      output_file: str,
                      session_info: Dict[str, Any] = None):
        """
        Export samples to a file in line protocol format

        Args:
            samples: List of sample dictionaries
            output_file: Output file path
            session_info: Optional session metadata
        """
        lines = self.format_line_protocol(samples, session_info)

        with open(output_file, 'w') as f:
            for line in lines:
                f.write(line + '\n')

        return len(lines)

    def _escape_tag(self, value: str) -> str:
        """Escape tag value for InfluxDB line protocol"""
        if not isinstance(value, str):
            value = str(value)
        # Escape spaces, commas, and equals signs in tags
        return value.replace(' ', '\\ ').replace(',', '\\,').replace('=', '\\=')

    def _escape_field(self, value: str) -> str:
        """Escape field string value for InfluxDB line protocol"""
        if not isinstance(value, str):
            value = str(value)
        # Escape quotes and backslashes in string fields
        return value.replace('\\', '\\\\').replace('"', '\\"')

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        if isinstance(timestamp_str, datetime):
            return timestamp_str

        # Try ISO format first
        try:
            return datetime.fromisoformat(timestamp_str)
        except:
            pass

        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except:
                continue

        # Fallback to now
        return datetime.now()

    def generate_import_commands(self, line_protocol_file: str,
                                 influx_version: str = "2.x") -> str:
        """
        Generate shell commands for importing into InfluxDB

        Args:
            line_protocol_file: Path to line protocol file
            influx_version: "1.x" or "2.x"

        Returns:
            String with import commands
        """
        if influx_version == "2.x":
            return f"""# InfluxDB 2.x Import Commands:
# Replace BUCKET, ORG, and TOKEN with your values

influx write \\
  --bucket YOUR_BUCKET \\
  --org YOUR_ORG \\
  --token YOUR_TOKEN \\
  --file {line_protocol_file}

# Or using curl:
curl -XPOST "http://localhost:8086/api/v2/write?org=YOUR_ORG&bucket=YOUR_BUCKET" \\
  --header "Authorization: Token YOUR_TOKEN" \\
  --data-binary @{line_protocol_file}
"""
        else:  # 1.x
            return f"""# InfluxDB 1.x Import Commands:
# Replace DATABASE with your database name

influx -database YOUR_DATABASE -import -path={line_protocol_file}

# Or using curl:
curl -XPOST 'http://localhost:8086/write?db=YOUR_DATABASE' \\
  --data-binary @{line_protocol_file}
"""
