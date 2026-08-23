"""Async MongoDB lifecycle with one shared Motor client for the API process."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

_settings = get_settings()
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _database
    # The queue lifecycle persists timezone-aware timestamps. Configure PyMongo/Motor
    # to read MongoDB BSON datetimes as aware values too, preventing naive/aware
    # subtraction errors when completing a consultation or calculating durations.
    _client = AsyncIOMotorClient(
        _settings.mongodb_url,
        serverSelectionTimeoutMS=_settings.mongodb_server_selection_timeout_ms,
        tz_aware=True,
    )
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
        from app.utils.errors import ServiceUnavailableError
        raise ServiceUnavailableError("MongoDB is unavailable; start MongoDB before using operational API endpoints.")
    return _database


async def is_mongo_ready() -> bool:
    if _client is None or _database is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False
