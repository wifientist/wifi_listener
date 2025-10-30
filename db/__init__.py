"""
Database package for WiFi metrics storage
"""

from .database import Database
from .schema import init_database

__all__ = ['Database', 'init_database']
