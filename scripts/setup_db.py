#!/usr/bin/env python
"""
Script for setting up the MongoDB database indexes.
"""

import logging

from config.settings import settings
from src.db.database import setup_indexes
from src.utils.logging import setup_logging

# Configure logging
setup_logging(level=settings.log_level)
logger = logging.getLogger(__name__)


def setup_database():
    """Create all database indexes."""
    try:
        logger.info("Creating database indexes...")
        setup_indexes()
        logger.info("Database indexes created successfully")

    except Exception as e:
        logger.exception(f"Error creating database indexes: {e}")
        raise


if __name__ == "__main__":
    setup_database()
