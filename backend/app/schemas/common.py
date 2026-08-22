"""Shared enums and response contracts for the OPD SmartQueue API."""
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict


class Role(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"


class TokenStatus(str, Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class Priority(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class DoctorStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    ON_BREAK = "ON_BREAK"
    OFFLINE = "OFFLINE"


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str


class MongoModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class TimestampedModel(MongoModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MessageResponse(MongoModel):
    message: str
    details: dict[str, Any] | None = None
