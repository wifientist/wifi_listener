"""
Database operations for WiFi metrics
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Any


class Database:
    """
    Database interface for WiFi metrics storage and retrieval
    """

    def __init__(self, db_path: str):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Open database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    # ==================== SESSION OPERATIONS ====================

    def create_session(self, location: str, ap_name: str = None,
                      notes: str = None, sample_interval: float = 4.0,
                      iperf3_enabled: bool = False, iperf3_server: str = None,
                      iperf3_port: int = 5201, iperf3_parallel: int = 1,
                      iperf3_reverse: bool = False, iperf3_udp: bool = False) -> int:
        """
        Create a new test session

        Args:
            location: Test location (e.g., "Kitchen - 20ft")
            ap_name: Access point name/identifier
            notes: Optional notes about the test
            sample_interval: Sampling interval in seconds
            iperf3_enabled: Whether iperf3 testing is enabled
            iperf3_server: iperf3 server IP/hostname
            iperf3_port: iperf3 server port
            iperf3_parallel: Number of parallel streams
            iperf3_reverse: Reverse mode (server sends)
            iperf3_udp: Use UDP instead of TCP

        Returns:
            int: Session ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (
                location, ap_name, notes, start_time, sample_interval_seconds,
                iperf3_enabled, iperf3_server, iperf3_port, iperf3_parallel,
                iperf3_reverse, iperf3_udp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (location, ap_name, notes, datetime.now(), sample_interval,
              iperf3_enabled, iperf3_server, iperf3_port, iperf3_parallel,
              iperf3_reverse, iperf3_udp))

        self.conn.commit()
        return cursor.lastrowid

    def end_session(self, session_id: int):
        """
        Mark a session as ended

        Args:
            session_id: ID of the session to end
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?
            WHERE id = ?
        """, (datetime.now(), session_id))
        self.conn.commit()

    def get_session(self, session_id: int) -> Optional[Dict]:
        """
        Get session details

        Args:
            session_id: Session ID

        Returns:
            dict: Session data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_active_session(self) -> Optional[Dict]:
        """
        Get the currently active session (end_time is NULL)

        Returns:
            dict: Active session data or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions
            WHERE end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """
        List all sessions

        Args:
            limit: Maximum number of sessions to return

        Returns:
            list: List of session dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions
            ORDER BY start_time DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== SAMPLE OPERATIONS ====================

    def insert_sample(self, session_id: int, sample_data: Dict[str, Any]) -> int:
        """
        Insert a WiFi sample reading

        Args:
            session_id: ID of the session this sample belongs to
            sample_data: Dictionary of sample metrics (including optional iperf3 throughput)

        Returns:
            int: Sample ID
        """
        # Add timestamp if not present
        if 'timestamp' not in sample_data:
            sample_data['timestamp'] = datetime.now()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO wifi_samples (
                session_id, timestamp, ssid, bssid,
                signal_dbm, noise_dbm, snr_db, tx_rate_mbps,
                iperf3_throughput_min_mbps, iperf3_throughput_avg_mbps, iperf3_throughput_max_mbps,
                channel, channel_width_mhz, frequency_band,
                phy_mode, mcs_index, security, country_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            sample_data.get('timestamp'),
            sample_data.get('ssid'),
            sample_data.get('bssid'),
            sample_data.get('signal_dbm'),
            sample_data.get('noise_dbm'),
            sample_data.get('snr_db'),
            sample_data.get('tx_rate_mbps'),
            sample_data.get('iperf3_throughput_min_mbps'),
            sample_data.get('iperf3_throughput_avg_mbps'),
            sample_data.get('iperf3_throughput_max_mbps'),
            sample_data.get('channel'),
            sample_data.get('channel_width_mhz'),
            sample_data.get('frequency_band'),
            sample_data.get('phy_mode'),
            sample_data.get('mcs_index'),
            sample_data.get('security'),
            sample_data.get('country_code')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_session_samples(self, session_id: int) -> List[Dict]:
        """
        Get all samples for a session

        Args:
            session_id: Session ID

        Returns:
            list: List of sample dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM wifi_samples
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_session_stats(self, session_id: int) -> Optional[Dict]:
        """
        Get statistical summary for a session

        Args:
            session_id: Session ID

        Returns:
            dict: Statistics (min/avg/max for key metrics including iperf3 throughput)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as sample_count,
                MIN(signal_dbm) as min_signal,
                AVG(signal_dbm) as avg_signal,
                MAX(signal_dbm) as max_signal,
                MIN(noise_dbm) as min_noise,
                AVG(noise_dbm) as avg_noise,
                MAX(noise_dbm) as max_noise,
                MIN(snr_db) as min_snr,
                AVG(snr_db) as avg_snr,
                MAX(snr_db) as max_snr,
                MIN(tx_rate_mbps) as min_tx_rate,
                AVG(tx_rate_mbps) as avg_tx_rate,
                MAX(tx_rate_mbps) as max_tx_rate,
                MIN(iperf3_throughput_min_mbps) as min_iperf3_throughput,
                AVG(iperf3_throughput_avg_mbps) as avg_iperf3_throughput,
                MAX(iperf3_throughput_max_mbps) as max_iperf3_throughput,
                MIN(mcs_index) as min_mcs,
                AVG(mcs_index) as avg_mcs,
                MAX(mcs_index) as max_mcs
            FROM wifi_samples
            WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_sample_count(self, session_id: int) -> int:
        """
        Get the number of samples for a session

        Args:
            session_id: Session ID

        Returns:
            int: Number of samples
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM wifi_samples WHERE session_id = ?
        """, (session_id,))
        return cursor.fetchone()[0]
