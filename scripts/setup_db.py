#!/usr/bin/env python
"""
Script for setting up the MongoDB database indexes.
"""

import logging
import asyncio

from src.config.settings import settings
from src.db.database import setup_indexes, async_db, COLLECTIONS
from scripts.seed_prompts import seed_prompts
from src.utils.logging import setup_logging

# Configure logging
setup_logging(level=settings.log_level)
logger = logging.getLogger(__name__)


async def setup_database():
    """Create all database indexes and seed default prompts."""
    try:
        # Create indexes
        logger.info("Creating database indexes...")
        setup_indexes()
        logger.info("Database indexes created successfully")

        # Reset existing prompt configs
        logger.info("Resetting existing prompt configurations...")
        result = await async_db[COLLECTIONS["prompt_configs"]].update_many(
            {"default": True},
            {"$set": {"default": False}}
        )
        logger.info(f"Reset {result.modified_count} existing prompt configurations")

        # Seed new prompt configs
        logger.info("Seeding default prompt configurations...")
        await seed_prompts()
        logger.info("Database setup completed successfully")

    except Exception as e:
        logger.exception(f"Error setting up database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_database())
