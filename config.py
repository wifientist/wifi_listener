"""
Configuration settings for WiFi listener
"""

import os

# Project paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
EXPORTS_DIR = os.path.join(PROJECT_DIR, 'exports')
DB_PATH = os.path.join(DATA_DIR, 'wifi_metrics.db')

# Sampling configuration
SAMPLE_INTERVAL_SECONDS = 4.0  # How often to collect metrics
DEFAULT_SESSION_DURATION_MINUTES = 5  # Auto-stop after this duration (0 = manual stop)

# System profiler settings
SYSTEM_PROFILER_TIMEOUT = 10  # Seconds before timing out

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
