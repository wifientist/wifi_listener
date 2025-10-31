#!/usr/bin/env python3
"""
Migration: Add wdutil fields to wifi_samples table

This migration adds fields from wdutil that provide additional WiFi metrics:
- cca_percent: Channel Clear Assessment (channel utilization %)
- guard_interval: Guard Interval in nanoseconds (800 or 3200)
- nss: Number of Spatial Streams (MIMO configuration)
"""

import sqlite3
import sys
import config

def migrate():
    """Add wdutil fields to existing wifi_samples table"""
    print("Migrating database to add wdutil fields...")
    print(f"Database: {config.DB_PATH}")

    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(wifi_samples)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'cca_percent' in columns:
            print("✓ Database already has wdutil fields - no migration needed")
            conn.close()
            return True

        print("Adding wdutil fields to wifi_samples table...")

        # Add wdutil fields
        migrations = [
            "ALTER TABLE wifi_samples ADD COLUMN cca_percent INTEGER",
            "ALTER TABLE wifi_samples ADD COLUMN guard_interval INTEGER",
            "ALTER TABLE wifi_samples ADD COLUMN nss INTEGER",
        ]

        for migration in migrations:
            print(f"  Running: {migration}")
            cursor.execute(migration)

        conn.commit()
        conn.close()

        print("✓ Migration complete!")
        print("\nNew fields added:")
        print("  - cca_percent: Channel utilization % (lower is better)")
        print("  - guard_interval: 800ns (short) or 3200ns (long)")
        print("  - nss: Number of spatial streams (e.g., 2 = 2x2 MIMO)")
        print("\nNote: These fields require wdutil access (sudo).")
        print("See docs for passwordless sudo configuration.")
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
