#!/usr/bin/env python3
"""
WiFi Listener - Rate@Range Testing Tool

Monitors WiFi connection metrics and stores them in a local database
for later analysis and visualization.
"""

import argparse
import sys
import time
import signal
import csv
import os
from datetime import datetime, timedelta

import config
from db import Database, init_database
from collectors import SystemProfilerCollector
from collectors.iperf3_runner import IPerf3Runner
from exporters import InfluxDBExporter


class WiFiListener:
    """Main application class for WiFi monitoring"""

    def __init__(self):
        self.collector = SystemProfilerCollector(timeout=config.SYSTEM_PROFILER_TIMEOUT)
        self.iperf3_runner = None
        self.db = None
        self.running = False
        self.current_session_id = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, _signum, _frame):
        """Handle interrupt signals (Ctrl+C)"""
        print("\n\nReceived interrupt signal. Stopping...")
        self.stop()
        sys.exit(0)

    def start_session(self, location: str, ap_name: str = None,
                     notes: str = None, duration_minutes: float = 0,
                     iperf3_server: str = None, iperf3_port: int = 5201,
                     iperf3_parallel: int = 1, iperf3_reverse: bool = False,
                     iperf3_udp: bool = False):
        """
        Start a new monitoring session

        Args:
            location: Test location description
            ap_name: Access point name/identifier
            notes: Optional notes
            duration_minutes: Auto-stop after this many minutes (0 = manual)
            iperf3_server: iperf3 server IP/hostname (None = no iperf3)
            iperf3_port: iperf3 server port (default: 5201)
            iperf3_parallel: Number of parallel streams (-P flag, default: 1)
            iperf3_reverse: Reverse mode - server sends to client (-R flag)
            iperf3_udp: Use UDP instead of TCP (-u flag)
        """
        # Initialize database
        init_database(config.DB_PATH)

        # Check if already running
        with Database(config.DB_PATH) as db:
            active = db.get_active_session()
            if active:
                print(f"ERROR: Session {active['id']} is already running!")
                print(f"  Location: {active['location']}")
                print(f"  Started: {active['start_time']}")
                print("\nPlease stop the active session first.")
                return False

        # Check WiFi connection
        if not self.collector.is_connected():
            print("ERROR: Not connected to WiFi!")
            print("Please connect to a WiFi network before starting a session.")
            return False

        # Get initial sample to show what we're monitoring
        initial_sample = self.collector.collect()
        if not initial_sample:
            print("ERROR: Could not collect initial WiFi sample")
            return False

        # Validate iperf3 if requested
        iperf3_enabled = iperf3_server is not None
        if iperf3_enabled:
            # Check if iperf3 is installed
            if not IPerf3Runner.check_iperf3_installed():
                print("ERROR: iperf3 not found. Install with: brew install iperf3")
                return False

            # Test server connectivity
            print(f"Testing connection to iperf3 server {iperf3_server}:{iperf3_port}...")
            if not IPerf3Runner.test_server_connection(iperf3_server, iperf3_port):
                print(f"WARNING: Could not connect to iperf3 server {iperf3_server}:{iperf3_port}")
                print("Continuing anyway - iperf3 will start when server becomes available")

        # Create session
        with Database(config.DB_PATH) as db:
            self.current_session_id = db.create_session(
                location=location,
                ap_name=ap_name,
                notes=notes,
                sample_interval=config.SAMPLE_INTERVAL_SECONDS,
                iperf3_enabled=iperf3_enabled,
                iperf3_server=iperf3_server,
                iperf3_port=iperf3_port,
                iperf3_parallel=iperf3_parallel,
                iperf3_reverse=iperf3_reverse,
                iperf3_udp=iperf3_udp
            )

        print("=" * 80)
        print("WiFi Monitoring Session Started")
        print("=" * 80)
        print(f"Session ID: {self.current_session_id}")
        print(f"Location: {location}")
        if ap_name:
            print(f"AP Name: {ap_name}")
        print(f"Connected to: {initial_sample['ssid']}")
        print(f"Sample Interval: {config.SAMPLE_INTERVAL_SECONDS} seconds")
        if duration_minutes > 0:
            print(f"Duration: {duration_minutes} minutes (auto-stop)")
        else:
            print("Duration: Manual stop (press Ctrl+C)")

        # Display iperf3 info
        if iperf3_enabled:
            print(f"\niperf3 Testing: ENABLED")
            print(f"  Server: {iperf3_server}:{iperf3_port}")
            print(f"  Parallel Streams: {iperf3_parallel}")
            if iperf3_reverse:
                print(f"  Mode: DOWNLOAD (server → client)")
            else:
                print(f"  Mode: UPLOAD (client → server)")
            if iperf3_udp:
                print(f"  Protocol: UDP")
            else:
                print(f"  Protocol: TCP")
        else:
            print(f"\niperf3 Testing: Disabled (passive monitoring)")

        print(f"\nDatabase: {config.DB_PATH}")
        print("=" * 80)
        print()

        # Initialize iperf3 runner if enabled
        if iperf3_enabled:
            self.iperf3_runner = IPerf3Runner(
                server=iperf3_server,
                port=iperf3_port,
                parallel=iperf3_parallel,
                reverse=iperf3_reverse,
                udp=iperf3_udp
            )

        # Start monitoring loop
        self._run_monitoring_loop(duration_minutes)

        return True

    def _run_monitoring_loop(self, duration_minutes: float):
        """
        Main monitoring loop

        Args:
            duration_minutes: Auto-stop after this many minutes (0 = manual)
        """
        self.running = True
        sample_count = 0
        start_time = datetime.now()
        end_time = None

        if duration_minutes > 0:
            end_time = start_time + timedelta(minutes=duration_minutes)

        # Start iperf3 if enabled
        if self.iperf3_runner:
            duration_seconds = int(duration_minutes * 60) if duration_minutes > 0 else 300
            self.iperf3_runner.start(duration=duration_seconds)

        print("Collecting samples... (press Ctrl+C to stop)")
        if self.iperf3_runner:
            print(f"{'Time':<20} {'Signal':>8} {'Noise':>8} {'SNR':>6} {'TX Rate':>10} {'iperf3':>12} {'Channel':>8}")
        else:
            print(f"{'Time':<20} {'Signal':>8} {'Noise':>8} {'SNR':>6} {'TX Rate':>10} {'Channel':>8}")
        print("-" * 95 if self.iperf3_runner else "-" * 80)

        try:
            while self.running:
                # Check if we should auto-stop
                if end_time and datetime.now() >= end_time:
                    print("\nDuration reached. Stopping...")
                    break

                # Collect sample
                sample = self.collector.collect()

                if sample:
                    # Get iperf3 throughput stats if available
                    if self.iperf3_runner and self.iperf3_runner.is_running():
                        throughput_stats = self.iperf3_runner.get_latest_throughput_stats()
                        if throughput_stats:
                            sample['iperf3_throughput_min_mbps'] = throughput_stats['min']
                            sample['iperf3_throughput_avg_mbps'] = throughput_stats['avg']
                            sample['iperf3_throughput_max_mbps'] = throughput_stats['max']

                    # Store in database
                    with Database(config.DB_PATH) as db:
                        db.insert_sample(self.current_session_id, sample)

                    sample_count += 1

                    # Display progress
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    signal_dbm = sample.get('signal_dbm', 'N/A')
                    noise_dbm = sample.get('noise_dbm', 'N/A')
                    snr_db = sample.get('snr_db', 'N/A')
                    tx_rate = sample.get('tx_rate_mbps', 'N/A')
                    channel = sample.get('channel', 'N/A')

                    if self.iperf3_runner:
                        iperf3_avg = sample.get('iperf3_throughput_avg_mbps')
                        iperf3_str = f"{iperf3_avg:.0f}" if iperf3_avg else "-"
                        print(f"{timestamp:<20} {signal_dbm:>8} {noise_dbm:>8} {snr_db:>6} {tx_rate:>10} {iperf3_str:>12} {channel:>8}")
                    else:
                        print(f"{timestamp:<20} {signal_dbm:>8} {noise_dbm:>8} {snr_db:>6} {tx_rate:>10} {channel:>8}")

                else:
                    print(f"{datetime.now().strftime('%H:%M:%S'):<20} WiFi disconnected!")

                # Wait for next sample
                time.sleep(config.SAMPLE_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n\nStopping...")

        # Stop iperf3 if running
        if self.iperf3_runner and self.iperf3_runner.is_running():
            self.iperf3_runner.stop()

        # End session
        with Database(config.DB_PATH) as db:
            db.end_session(self.current_session_id)

        elapsed = datetime.now() - start_time

        print("\n" + "=" * 80)
        print("Session Complete")
        print("=" * 80)
        print(f"Session ID: {self.current_session_id}")
        print(f"Samples Collected: {sample_count}")
        print(f"Duration: {elapsed.total_seconds():.1f} seconds")
        print(f"Database: {config.DB_PATH}")
        print("=" * 80)

        self.running = False

    def stop(self):
        """Stop the monitoring loop"""
        self.running = False

    def stop_session(self, session_id: int = None):
        """
        Manually stop/close an active session

        Args:
            session_id: Session ID to stop (None = stop active session)
        """
        init_database(config.DB_PATH)

        with Database(config.DB_PATH) as db:
            if session_id is None:
                # Find active session
                session = db.get_active_session()
                if not session:
                    print("No active session found")
                    return
                session_id = session['id']
            else:
                session = db.get_session(session_id)
                if not session:
                    print(f"ERROR: Session {session_id} not found")
                    return

            # End the session
            db.end_session(session_id)
            sample_count = db.get_sample_count(session_id)

        print(f"\n✓ Session {session_id} stopped")
        print(f"  Location: {session['location']}")
        print(f"  AP Name: {session['ap_name'] or 'N/A'}")
        print(f"  Samples collected: {sample_count}")

    def list_sessions(self, limit: int = 20):
        """
        List all sessions

        Args:
            limit: Maximum number of sessions to show
        """
        init_database(config.DB_PATH)

        with Database(config.DB_PATH) as db:
            sessions = db.list_sessions(limit=limit)

        if not sessions:
            print("No sessions found.")
            return

        print("\n" + "=" * 90)
        print("Sessions")
        print("=" * 90)
        print(f"{'ID':<6} {'Location':<22} {'AP Name':<15} {'iperf3':<12} {'Start Time':<20} {'Samples':<8}")
        print("-" * 90)

        for session in sessions:
            session_id = session['id']
            location = session['location'][:21]
            ap_name = (session['ap_name'] or 'N/A')[:14]
            start_time = session['start_time'][:19]

            # Get sample count
            with Database(config.DB_PATH) as db:
                sample_count = db.get_sample_count(session_id)

            # Show iperf3 status
            if session.get('iperf3_enabled'):
                iperf3_info = f"Yes"
                if session.get('iperf3_parallel', 1) > 1:
                    iperf3_info += f"(P{session['iperf3_parallel']})"
                if session.get('iperf3_reverse'):
                    iperf3_info += "/R"
            else:
                iperf3_info = "No"

            status = "" if session['end_time'] else " (active)"
            print(f"{session_id:<6} {location:<22} {ap_name:<15} {iperf3_info:<12} {start_time:<20} {sample_count:<8}{status}")

        print("=" * 90)

    def show_stats(self, session_id: int):
        """
        Show statistics for a session

        Args:
            session_id: Session ID
        """
        init_database(config.DB_PATH)

        with Database(config.DB_PATH) as db:
            session = db.get_session(session_id)
            if not session:
                print(f"ERROR: Session {session_id} not found")
                return

            stats = db.get_session_stats(session_id)
            if not stats or stats['sample_count'] == 0:
                print(f"ERROR: No samples found for session {session_id}")
                return

        print("\n" + "=" * 80)
        print(f"Session Statistics - ID {session_id}")
        print("=" * 80)
        print(f"Location: {session['location']}")
        if session['ap_name']:
            print(f"AP Name: {session['ap_name']}")
        print(f"Start Time: {session['start_time']}")
        print(f"End Time: {session['end_time'] or 'In Progress'}")
        print(f"Sample Count: {stats['sample_count']}")

        # Show iperf3 configuration if enabled
        if session.get('iperf3_enabled'):
            print(f"\niperf3 Testing: ENABLED")
            print(f"  Server: {session['iperf3_server']}:{session['iperf3_port']}")
            print(f"  Parallel Streams: {session['iperf3_parallel']}")
            mode = "DOWNLOAD (server → client)" if session['iperf3_reverse'] else "UPLOAD (client → server)"
            print(f"  Mode: {mode}")
            protocol = "UDP" if session['iperf3_udp'] else "TCP"
            print(f"  Protocol: {protocol}")
        else:
            print(f"\niperf3 Testing: Disabled (passive monitoring)")
        print()

        print("Metrics Summary:")
        print("-" * 80)
        print(f"{'Metric':<20} {'Min':>12} {'Average':>12} {'Max':>12} {'Unit':>8}")
        print("-" * 80)

        metrics = [
            ('Signal (RSSI)', 'signal', 'dBm'),
            ('Noise Floor', 'noise', 'dBm'),
            ('SNR', 'snr', 'dB'),
            ('TX Rate', 'tx_rate', 'Mbps'),
            ('MCS Index', 'mcs', ''),
        ]

        # Add iperf3 throughput if data is available
        if session.get('iperf3_enabled') and stats.get('avg_iperf3_throughput') is not None:
            metrics.append(('iperf3 Throughput', 'iperf3_throughput', 'Mbps'))

        for label, key, unit in metrics:
            min_val = stats.get(f'min_{key}')
            avg_val = stats.get(f'avg_{key}')
            max_val = stats.get(f'max_{key}')

            if min_val is not None:
                min_str = f"{min_val:.1f}" if isinstance(min_val, float) else str(min_val)
                avg_str = f"{avg_val:.1f}" if isinstance(avg_val, float) else str(avg_val)
                max_str = f"{max_val:.1f}" if isinstance(max_val, float) else str(max_val)

                print(f"{label:<20} {min_str:>12} {avg_str:>12} {max_str:>12} {unit:>8}")

        print("=" * 80)

    def export_csv(self, session_id: int, output_file: str = None):
        """
        Export session data to CSV format

        Args:
            session_id: Session ID
            output_file: Output file path (auto-generated if None)
        """
        init_database(config.DB_PATH)

        with Database(config.DB_PATH) as db:
            session = db.get_session(session_id)
            if not session:
                print(f"ERROR: Session {session_id} not found")
                return

            samples = db.get_session_samples(session_id)
            if not samples:
                print(f"ERROR: No samples found for session {session_id}")
                return

        # Generate filename if not provided
        if not output_file:
            filename = f"session_{session_id}_{session['location'].replace(' ', '_')}.csv"
            output_file = os.path.join(config.EXPORTS_DIR, filename)

        # Write CSV
        fieldnames = [
            'timestamp', 'ssid', 'signal_dbm', 'noise_dbm', 'snr_db',
            'tx_rate_mbps', 'iperf3_throughput_min_mbps', 'iperf3_throughput_avg_mbps',
            'iperf3_throughput_max_mbps', 'channel', 'channel_width_mhz', 'frequency_band',
            'phy_mode', 'mcs_index', 'security'
        ]

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(samples)

        print(f"\nExported {len(samples)} samples to: {output_file}")
        print(f"Session: {session['location']} (AP: {session['ap_name'] or 'N/A'})")

    def export_influxdb(self, session_id: int, output_file: str = None,
                       influx_version: str = "2.x"):
        """
        Export session data to InfluxDB line protocol format

        Args:
            session_id: Session ID
            output_file: Output file path (auto-generated if None)
            influx_version: "1.x" or "2.x" for command generation
        """
        init_database(config.DB_PATH)

        with Database(config.DB_PATH) as db:
            session = db.get_session(session_id)
            if not session:
                print(f"ERROR: Session {session_id} not found")
                return

            samples = db.get_session_samples(session_id)
            if not samples:
                print(f"ERROR: No samples found for session {session_id}")
                return

        # Generate filename if not provided
        if not output_file:
            filename = f"session_{session_id}_influx.txt"
            output_file = os.path.join(config.EXPORTS_DIR, filename)

        # Export to line protocol
        exporter = InfluxDBExporter()
        num_lines = exporter.export_to_file(samples, output_file, session_info=session)

        print(f"\n✓ Exported {num_lines} data points to: {output_file}")
        print(f"  Session: {session['location']} (AP: {session['ap_name'] or 'N/A'})")
        print(f"  Format: InfluxDB Line Protocol")
        print()
        print("=" * 80)
        print("Import Instructions:")
        print("=" * 80)
        print(exporter.generate_import_commands(output_file, influx_version))

    def compare_sessions(self, session_ids: list):
        """
        Compare statistics across multiple sessions

        Args:
            session_ids: List of session IDs to compare
        """
        init_database(config.DB_PATH)

        sessions_data = []

        with Database(config.DB_PATH) as db:
            for sid in session_ids:
                session = db.get_session(sid)
                if not session:
                    print(f"WARNING: Session {sid} not found, skipping")
                    continue

                stats = db.get_session_stats(sid)
                if not stats or stats['sample_count'] == 0:
                    print(f"WARNING: No samples for session {sid}, skipping")
                    continue

                sessions_data.append({
                    'id': sid,
                    'session': session,
                    'stats': stats
                })

        if not sessions_data:
            print("ERROR: No valid sessions to compare")
            return

        print("\n" + "=" * 120)
        print("Session Comparison")
        print("=" * 120)

        # Header
        print(f"{'ID':<4} {'Location':<25} {'AP':<15} {'Samples':>8} {'Avg Signal':>12} {'Avg SNR':>10} {'Avg TX Rate':>12}")
        print("-" * 120)

        for data in sessions_data:
            sid = data['id']
            session = data['session']
            stats = data['stats']

            location = session['location'][:24]
            ap = (session['ap_name'] or 'N/A')[:14]
            samples = stats['sample_count']
            avg_signal = f"{stats['avg_signal']:.1f} dBm" if stats['avg_signal'] else 'N/A'
            avg_snr = f"{stats['avg_snr']:.1f} dB" if stats['avg_snr'] else 'N/A'
            avg_rate = f"{stats['avg_tx_rate']:.0f} Mbps" if stats['avg_tx_rate'] else 'N/A'

            print(f"{sid:<4} {location:<25} {ap:<15} {samples:>8} {avg_signal:>12} {avg_snr:>10} {avg_rate:>12}")

        print("=" * 120)

        # Detailed comparison
        print("\nDetailed Metrics Comparison:")
        print("-" * 120)

        metrics = [
            ('Signal (RSSI)', 'signal', 'dBm'),
            ('Noise Floor', 'noise', 'dBm'),
            ('SNR', 'snr', 'dB'),
            ('TX Rate', 'tx_rate', 'Mbps'),
            ('MCS Index', 'mcs', ''),
        ]

        for metric_label, metric_key, unit in metrics:
            print(f"\n{metric_label}:")
            print(f"  {'Session':<4} {'Location':<25} {'Min':>12} {'Avg':>12} {'Max':>12}")
            print("  " + "-" * 70)

            for data in sessions_data:
                sid = data['id']
                location = data['session']['location'][:24]
                stats = data['stats']

                min_val = stats.get(f'min_{metric_key}')
                avg_val = stats.get(f'avg_{metric_key}')
                max_val = stats.get(f'max_{metric_key}')

                if min_val is not None:
                    min_str = f"{min_val:.1f}" if isinstance(min_val, float) else str(int(min_val))
                    avg_str = f"{avg_val:.1f}" if isinstance(avg_val, float) else str(int(avg_val))
                    max_str = f"{max_val:.1f}" if isinstance(max_val, float) else str(int(max_val))

                    if unit:
                        min_str += f" {unit}"
                        avg_str += f" {unit}"
                        max_str += f" {unit}"

                    print(f"  {sid:<4} {location:<25} {min_str:>12} {avg_str:>12} {max_str:>12}")

        print("\n" + "=" * 120)


def main():
    """Main entry point"""
    epilog_text = """
Examples:
  # Passive monitoring (no iperf3)
  %(prog)s start -l "Kitchen - 20ft" -a "R770" -d 5

  # Upload test with iperf3 (4 parallel streams)
  %(prog)s start -l "Kitchen - 20ft" -a "R770" -d 5 \\
    --iperf3-server 192.168.1.100 -P 4

  # Download test (reverse mode)
  %(prog)s start -l "Kitchen - 20ft" -a "R770" -d 5 \\
    --iperf3-server 192.168.1.100 -P 4 -R

  # List all sessions
  %(prog)s list

  # View session statistics
  %(prog)s stats 1

  # Export to CSV
  %(prog)s export 1

  # Export to InfluxDB format
  %(prog)s influx 1

  # Compare multiple sessions
  %(prog)s compare 1 2 3

For iperf3 setup: See IPERF3_QUICKSTART.md
For Grafana setup: See GRAFANA_SETUP.md
    """

    parser = argparse.ArgumentParser(
        description='WiFi Listener - Rate@Range Testing Tool',
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Start command
    start_help = """
Start a WiFi monitoring session.

Basic Usage:
  Passive monitoring: -l LOCATION -a AP_NAME -d MINUTES
  With iperf3: Add --iperf3-server IP and optional -P, -R, -u flags

Examples:
  # 5-minute passive test
  start -l "Kitchen - 20ft" -a "R770" -d 5

  # Upload test using .env defaults
  start -l "Kitchen" -a "R770" -d 5 --iperf3

  # Upload test with explicit server and streams
  start -l "Kitchen" -a "R770" -d 5 --iperf3-server 192.168.1.100 -P 4

  # Download test using .env server, override parallel streams
  start -l "Kitchen" -a "R770" -d 5 --iperf3 -P 8 -R
    """
    start_parser = subparsers.add_parser('start',
                                         help='Start a monitoring session',
                                         description=start_help,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)

    # Basic options
    start_parser.add_argument('--location', '-l', required=True,
                             help='Test location (e.g., "Kitchen - 20ft")')
    start_parser.add_argument('--ap-name', '-a',
                             help='Access point name/identifier (e.g., "R770", "AP1")')
    start_parser.add_argument('--notes', '-n',
                             help='Optional notes about this test')
    start_parser.add_argument('--duration', '-d', type=float,
                             default=config.DEFAULT_SESSION_DURATION_MINUTES,
                             help='Auto-stop after N minutes (default: %(default)s, 0 = manual stop)')

    # iperf3 options
    iperf3_group = start_parser.add_argument_group('iperf3 options (active throughput testing)')
    iperf3_group.add_argument('--iperf3',
                             action='store_true',
                             help='Enable iperf3 using .env defaults (requires IPERF3_SERVER in .env)')
    iperf3_group.add_argument('--iperf3-server',
                             default=None,
                             metavar='IP',
                             help='iperf3 server IP/hostname (overrides .env IPERF3_SERVER)')
    iperf3_group.add_argument('--iperf3-port',
                             type=int,
                             default=None,
                             metavar='PORT',
                             help='iperf3 server port (overrides .env, default: 5201)')
    iperf3_group.add_argument('--iperf3-parallel', '-P',
                             type=int,
                             default=None,
                             metavar='N',
                             help='Number of parallel streams (overrides .env, recommended: 4)')
    iperf3_group.add_argument('--iperf3-reverse', '-R',
                             action='store_true',
                             help='Reverse mode: download test (server → client)')
    iperf3_group.add_argument('--iperf3-udp', '-u',
                             action='store_true',
                             help='Use UDP instead of TCP')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop/close an active session')
    stop_parser.add_argument('session_id', type=int, nargs='?',
                            help='Session ID to stop (default: stop active session)')

    # List command
    list_parser = subparsers.add_parser('list', help='List all sessions')
    list_parser.add_argument('--limit', type=int, default=20,
                            help='Maximum number of sessions to show')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show session statistics')
    stats_parser.add_argument('session_id', type=int,
                             help='Session ID')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export session data to CSV')
    export_parser.add_argument('session_id', type=int,
                              help='Session ID')
    export_parser.add_argument('--output', '-o',
                              help='Output file path (auto-generated if not specified)')

    # InfluxDB export command
    influx_parser = subparsers.add_parser('influx', help='Export session to InfluxDB format')
    influx_parser.add_argument('session_id', type=int,
                              help='Session ID')
    influx_parser.add_argument('--output', '-o',
                              help='Output file path (auto-generated if not specified)')
    influx_parser.add_argument('--version', '-v', choices=['1.x', '2.x'], default='2.x',
                              help='InfluxDB version (for import commands)')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple sessions')
    compare_parser.add_argument('session_ids', type=int, nargs='+',
                               help='Session IDs to compare (space-separated)')

    args = parser.parse_args()

    # Create app instance
    app = WiFiListener()

    if args.command == 'start':
        # Handle iperf3 flag logic
        # Priority: CLI args > --iperf3 flag > .env defaults
        iperf3_server = args.iperf3_server
        iperf3_port = args.iperf3_port if args.iperf3_port is not None else config.IPERF3_DEFAULT_PORT
        iperf3_parallel = args.iperf3_parallel if args.iperf3_parallel is not None else config.IPERF3_DEFAULT_PARALLEL

        # For reverse and udp, check if explicitly set via CLI, otherwise use .env defaults
        iperf3_reverse = args.iperf3_reverse if args.iperf3_reverse else config.IPERF3_DEFAULT_REVERSE
        iperf3_udp = args.iperf3_udp if args.iperf3_udp else config.IPERF3_DEFAULT_UDP

        # If --iperf3 flag used, enable with .env defaults
        if args.iperf3:
            if not iperf3_server:  # No explicit --iperf3-server
                iperf3_server = config.IPERF3_DEFAULT_SERVER
                if not iperf3_server:
                    print("ERROR: --iperf3 requires IPERF3_SERVER to be set in .env file")
                    print("Either:")
                    print("  1. Set IPERF3_SERVER in .env, or")
                    print("  2. Use --iperf3-server IP instead of --iperf3")
                    sys.exit(1)

        app.start_session(
            location=args.location,
            ap_name=args.ap_name,
            notes=args.notes,
            duration_minutes=args.duration,
            iperf3_server=iperf3_server,
            iperf3_port=iperf3_port,
            iperf3_parallel=iperf3_parallel,
            iperf3_reverse=iperf3_reverse,
            iperf3_udp=iperf3_udp
        )

    elif args.command == 'stop':
        app.stop_session(args.session_id)

    elif args.command == 'list':
        app.list_sessions(limit=args.limit)

    elif args.command == 'stats':
        app.show_stats(args.session_id)

    elif args.command == 'export':
        app.export_csv(args.session_id, args.output)

    elif args.command == 'influx':
        app.export_influxdb(args.session_id, args.output, args.version)

    elif args.command == 'compare':
        app.compare_sessions(args.session_ids)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
