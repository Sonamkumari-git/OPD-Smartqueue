"""Async MongoDB lifecycle with one shared Motor client for the API process."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

_settings = get_settings()
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _database
    _client = AsyncIOMotorClient(_settings.mongodb_url, serverSelectionTimeoutMS=4000)
    await _client.admin.command("ping")
    _database = _client[_settings.database_name]


async def close_mongo_connection() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("MongoDB is not connected. Start MongoDB before starting the API.")
    return _database
