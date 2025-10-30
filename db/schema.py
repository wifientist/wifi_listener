"""
Database schema for WiFi metrics
"""

import sqlite3
from datetime import datetime

# SQL schema definitions
SCHEMA_SQL = """
-- Sessions table: tracks each test session
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    notes TEXT,
    ap_name TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    sample_interval_seconds REAL DEFAULT 4.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WiFi samples table: individual metric readings
CREATE TABLE IF NOT EXISTS wifi_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Connection Info
    ssid TEXT NOT NULL,
    bssid TEXT,

    -- Signal Quality
    signal_dbm INTEGER,
    noise_dbm INTEGER,
    snr_db INTEGER,

    -- Performance Metrics
    tx_rate_mbps INTEGER,

    -- Channel Info
    channel INTEGER,
    channel_width_mhz INTEGER,
    frequency_band TEXT,

    -- Protocol Info
    phy_mode TEXT,
    mcs_index INTEGER,

    -- Additional
    security TEXT,
    country_code TEXT,

    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_samples_session ON wifi_samples(session_id);
CREATE INDEX IF NOT EXISTS idx_samples_timestamp ON wifi_samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time);
"""


def init_database(db_path):
    """
    Initialize the database with schema.

    Args:
        db_path: Path to SQLite database file

    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def get_schema_version(db_path):
    """
    Get the current schema version (for future migrations)

    Returns:
        int: Schema version number
    """
    # For now, just return 1
    # In future, we can track this in a schema_version table
    return 1
