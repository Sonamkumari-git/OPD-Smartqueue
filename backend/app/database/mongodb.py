"""Async MongoDB lifecycle with one shared Motor client for the API process."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import AutoReconnect, ServerSelectionTimeoutError
from app.config import get_settings

_settings = get_settings()
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _database
    # The queue lifecycle persists timezone-aware timestamps. Configure PyMongo/Motor
    # to read MongoDB BSON datetimes as aware values too, preventing naive/aware
    # subtraction errors when completing a consultation or calculating durations.
    for attempt in range(3):
        candidate = AsyncIOMotorClient(
            _settings.mongodb_url,
            serverSelectionTimeoutMS=_settings.mongodb_server_selection_timeout_ms,
            tz_aware=True,
        )
        try:
            await candidate.admin.command("ping")
            _client = candidate
            _database = candidate[_settings.database_name]
            return
        except (AutoReconnect, ServerSelectionTimeoutError):
            candidate.close()
            if attempt == 2:
                raise
            await asyncio.sleep(1.5 * (attempt + 1))


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
