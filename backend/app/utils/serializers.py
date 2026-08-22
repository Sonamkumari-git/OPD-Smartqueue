"""Explicit conversion of MongoDB document identifiers for JSON response payloads."""
from datetime import date, datetime
from bson import ObjectId


def as_object_id(value: str, field_name: str = "id") -> ObjectId:
    if not ObjectId.is_valid(value):
        from app.utils.errors import AppError
        raise AppError(f"Invalid {field_name}.", "INVALID_ID", 422)
    return ObjectId(value)


def serialize_document(document: dict | None) -> dict | None:
    if document is None:
        return None
    serialized: dict = {}
    for key, value in document.items():
        if key == "_id":
            serialized["id"] = str(value)
        elif isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, (datetime, date)):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_document(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_document(item) if isinstance(item, dict) else str(item) if isinstance(item, ObjectId) else item for item in value]
        else:
            serialized[key] = value
    return serialized


def utc_now() -> datetime:
    return datetime.now().astimezone()
