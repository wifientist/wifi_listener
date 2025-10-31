#!/usr/bin/env python3
"""
Migration: Add iperf3 throughput columns to wifi_samples table

This migration adds the iperf3 throughput statistics columns (min/avg/max)
that capture active throughput data aligned with WiFi sample intervals.
"""

import sqlite3
import sys
import config

def migrate():
    """Add iperf3 throughput columns to existing wifi_samples table"""
    print("Migrating database to add iperf3 throughput columns...")
    print(f"Database: {config.DB_PATH}")

    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(wifi_samples)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'iperf3_throughput_avg_mbps' in columns:
            print("✓ Database already has iperf3 throughput columns - no migration needed")
            conn.close()
            return True

        print("Adding iperf3 throughput columns to wifi_samples table...")

        # Add iperf3 throughput columns
        migrations = [
            "ALTER TABLE wifi_samples ADD COLUMN iperf3_throughput_min_mbps REAL",
            "ALTER TABLE wifi_samples ADD COLUMN iperf3_throughput_avg_mbps REAL",
            "ALTER TABLE wifi_samples ADD COLUMN iperf3_throughput_max_mbps REAL",
        ]

        for migration in migrations:
            print(f"  Running: {migration}")
            cursor.execute(migration)

        conn.commit()
        conn.close()

        print("✓ Migration complete!")
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
