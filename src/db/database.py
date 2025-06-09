"""
Database connection and session management for MongoDB.
"""

from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient

from config.settings import settings

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
    "orders": "orders",
}


# Create indexes
def setup_indexes():
    """Create necessary indexes for collections."""
    # PromptConfig indexes
    db[COLLECTIONS["prompt_configs"]].create_index("name", unique=True)

    # Stock indexes
    db[COLLECTIONS["stocks"]].create_index("ticker", unique=True)
    db[COLLECTIONS["stocks"]].create_index("modified_time")

    # Forecast indexes
    db[COLLECTIONS["forecasts"]].create_index(
        [("stock_ticker", 1), ("forecast_date", 1)]
    )
    db[COLLECTIONS["forecasts"]].create_index("created_time")

    # Basket indexes
    db[COLLECTIONS["baskets"]].create_index("creation_date")

    # Order indexes
    db[COLLECTIONS["orders"]].create_index([("stock_ticker", 1), ("placed_time", 1)])
    db[COLLECTIONS["orders"]].create_index("demat_account")


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Get async database instance."""
    try:
        yield async_db
    finally:
        pass  # Connection is managed by the client
