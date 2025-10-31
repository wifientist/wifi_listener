"""
Configuration settings for WiFi listener
"""

import os
from pathlib import Path

# Load .env file if it exists
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

load_env()

# Project paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, os.getenv('DATABASE_PATH', 'data').split('/')[0])
EXPORTS_DIR = os.path.join(PROJECT_DIR, os.getenv('EXPORTS_PATH', 'exports'))
DB_PATH = os.path.join(PROJECT_DIR, os.getenv('DATABASE_PATH', 'data/wifi_metrics.db'))

# Sampling configuration
SAMPLE_INTERVAL_SECONDS = float(os.getenv('SAMPLE_INTERVAL_SECONDS', '4.0'))
DEFAULT_SESSION_DURATION_MINUTES = float(os.getenv('DEFAULT_DURATION_MINUTES', '5'))

# iperf3 defaults
IPERF3_DEFAULT_SERVER = os.getenv('IPERF3_SERVER', '')
IPERF3_DEFAULT_PORT = int(os.getenv('IPERF3_PORT', '5201'))
IPERF3_DEFAULT_PARALLEL = int(os.getenv('IPERF3_PARALLEL', '1'))
IPERF3_DEFAULT_REVERSE = os.getenv('IPERF3_REVERSE', 'false').lower() in ('true', '1', 'yes')
IPERF3_DEFAULT_UDP = os.getenv('IPERF3_UDP', 'false').lower() in ('true', '1', 'yes')

# System profiler settings
SYSTEM_PROFILER_TIMEOUT = 10  # Seconds before timing out

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
