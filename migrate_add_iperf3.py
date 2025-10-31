#!/usr/bin/env python3
"""
Migration: Add iperf3 columns to sessions table

This migration adds the iperf3-related columns that were added
after the initial schema was created.
"""

import sqlite3
import sys
import config

def migrate():
    """Add iperf3 columns to existing sessions table"""
    print("Migrating database to add iperf3 columns...")
    print(f"Database: {config.DB_PATH}")

    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'iperf3_enabled' in columns:
            print("✓ Database already has iperf3 columns - no migration needed")
            conn.close()
            return True

        print("Adding iperf3 columns to sessions table...")

        # Add iperf3 columns
        migrations = [
            "ALTER TABLE sessions ADD COLUMN iperf3_enabled BOOLEAN DEFAULT 0",
            "ALTER TABLE sessions ADD COLUMN iperf3_server TEXT",
            "ALTER TABLE sessions ADD COLUMN iperf3_port INTEGER DEFAULT 5201",
            "ALTER TABLE sessions ADD COLUMN iperf3_parallel INTEGER DEFAULT 1",
            "ALTER TABLE sessions ADD COLUMN iperf3_reverse BOOLEAN DEFAULT 0",
            "ALTER TABLE sessions ADD COLUMN iperf3_udp BOOLEAN DEFAULT 0",
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
