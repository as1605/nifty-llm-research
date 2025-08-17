"""
Database connection and session management for MongoDB.
"""

from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient

from src.config.settings import settings

# Create MongoDB client
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_db_name]

# Create async MongoDB client
async_client = AsyncIOMotorClient(settings.mongodb_uri)
async_db = async_client[settings.mongodb_db_name]

# Collection names
COLLECTIONS = {
    "prompt_configs": "prompt_configs",
    "invocations": "invocations",
    "stocks": "stocks",
    "forecasts": "forecasts",
    "baskets": "baskets",
    "zerodha_tokens": "zerodha_tokens",
}


# Create indexes
def setup_indexes():
    """Create necessary indexes for collections."""
    db[COLLECTIONS["prompt_configs"]].drop_indexes()

    # Stock indexes
    db[COLLECTIONS["stocks"]].create_index([("ticker", 1)], unique=True)
    db[COLLECTIONS["stocks"]].create_index([("indices", 1)])  # For filtering stocks by index
    db[COLLECTIONS["stocks"]].create_index([("modified_time", -1)])  # For recent updates

    # Forecast indexes
    db[COLLECTIONS["forecasts"]].create_index([
        ("stock_ticker", 1),
        ("created_time", -1)
    ])  # For recent forecasts
    db[COLLECTIONS["forecasts"]].create_index([
        ("stock_ticker", 1),
        ("forecast_date", 1)
    ])  # For forecast lookups
    db[COLLECTIONS["forecasts"]].create_index([("gain", -1)])  # For sorting by gain

    # Basket indexes
    db[COLLECTIONS["baskets"]].create_index([("creation_date", -1)])  # For recent baskets
    db[COLLECTIONS["baskets"]].create_index([("invocation_id", 1)])  # For linking to invocations

    # Zerodha token indexes
    db[COLLECTIONS["zerodha_tokens"]].create_index([("user_id", 1)], unique=True)  # One token per user
    db[COLLECTIONS["zerodha_tokens"]].create_index([("is_active", 1)])  # For finding active tokens
    db[COLLECTIONS["zerodha_tokens"]].create_index([("created_time", -1)])  # For recent tokens


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Get async database instance."""
    try:
        yield async_db
    finally:
        pass  # Connection is managed by the client
