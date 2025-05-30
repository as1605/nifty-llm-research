#!/usr/bin/env python
"""
Script for setting up the MongoDB database indexes.
"""
import logging

from src.db.database import setup_indexes
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Create all database indexes."""
    try:
        logger.info("Creating database indexes...")
        setup_indexes()
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise

if __name__ == "__main__":
    setup_database() 