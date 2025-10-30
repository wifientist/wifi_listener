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
from exporters import InfluxDBExporter


class WiFiListener:
    """Main application class for WiFi monitoring"""

    def __init__(self):
        self.collector = SystemProfilerCollector(timeout=config.SYSTEM_PROFILER_TIMEOUT)
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
                     notes: str = None, duration_minutes: float = 0):
        """
        Start a new monitoring session

        Args:
            location: Test location description
            ap_name: Access point name/identifier
            notes: Optional notes
            duration_minutes: Auto-stop after this many minutes (0 = manual)
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

        # Create session
        with Database(config.DB_PATH) as db:
            self.current_session_id = db.create_session(
                location=location,
                ap_name=ap_name,
                notes=notes,
                sample_interval=config.SAMPLE_INTERVAL_SECONDS
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
        print(f"Database: {config.DB_PATH}")
        print("=" * 80)
        print()

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

        print("Collecting samples... (press Ctrl+C to stop)")
        print(f"{'Time':<20} {'Signal':>8} {'Noise':>8} {'SNR':>6} {'TX Rate':>10} {'Channel':>8}")
        print("-" * 80)

        try:
            while self.running:
                # Check if we should auto-stop
                if end_time and datetime.now() >= end_time:
                    print("\nDuration reached. Stopping...")
                    break

                # Collect sample
                sample = self.collector.collect()

                if sample:
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

                    print(f"{timestamp:<20} {signal_dbm:>8} {noise_dbm:>8} {snr_db:>6} {tx_rate:>10} {channel:>8}")

                else:
                    print(f"{datetime.now().strftime('%H:%M:%S'):<20} WiFi disconnected!")

                # Wait for next sample
                time.sleep(config.SAMPLE_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n\nStopping...")

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

        print("\n" + "=" * 80)
        print("Sessions")
        print("=" * 80)
        print(f"{'ID':<6} {'Location':<25} {'AP Name':<20} {'Start Time':<20} {'Samples':<8}")
        print("-" * 80)

        for session in sessions:
            session_id = session['id']
            location = session['location'][:24]
            ap_name = (session['ap_name'] or 'N/A')[:19]
            start_time = session['start_time'][:19]

            # Get sample count
            with Database(config.DB_PATH) as db:
                sample_count = db.get_sample_count(session_id)

            status = "" if session['end_time'] else " (active)"
            print(f"{session_id:<6} {location:<25} {ap_name:<20} {start_time:<20} {sample_count:<8}{status}")

        print("=" * 80)

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
            'tx_rate_mbps', 'channel', 'channel_width_mhz', 'frequency_band',
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
    parser = argparse.ArgumentParser(
        description='WiFi Listener - Rate@Range Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a monitoring session')
    start_parser.add_argument('--location', '-l', required=True,
                             help='Test location (e.g., "Kitchen - 20ft")')
    start_parser.add_argument('--ap-name', '-a',
                             help='Access point name/identifier')
    start_parser.add_argument('--notes', '-n',
                             help='Optional notes about this test')
    start_parser.add_argument('--duration', '-d', type=float,
                             default=config.DEFAULT_SESSION_DURATION_MINUTES,
                             help='Auto-stop after N minutes (0 = manual stop)')

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
        app.start_session(
            location=args.location,
            ap_name=args.ap_name,
            notes=args.notes,
            duration_minutes=args.duration
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
