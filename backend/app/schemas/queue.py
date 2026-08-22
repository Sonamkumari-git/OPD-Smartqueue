"""Queue, token, department, doctor, and notification API contracts."""
from datetime import datetime
from pydantic import BaseModel
from app.schemas.common import DoctorStatus, Priority, TokenStatus


class DepartmentPublic(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    is_active: bool


class DoctorPublic(BaseModel):
    id: str
    user_id: str
    name: str
    department_id: str
    department_name: str | None = None
    specialization: str
    status: DoctorStatus


class TokenCreateRequest(BaseModel):
    department_id: str
    doctor_id: str
    priority: Priority = Priority.NORMAL


class TokenPublic(BaseModel):
    id: str
    token_number: str
    patient_id: str
    doctor_id: str
    department_id: str
    status: TokenStatus
    priority: Priority
    queue_date: str
    created_at: datetime
    called_at: datetime | None = None
    consultation_started_at: datetime | None = None
    completed_at: datetime | None = None


class QueuePosition(BaseModel):
    token_id: str
    token_number: str
    position: int | None
    patients_ahead: int
    queue_length: int
    currently_serving: str | None
    doctor_status: DoctorStatus
    estimated_wait_minutes: int
    estimate_lower_minutes: int
    estimate_upper_minutes: int
    recommended_return_at: datetime | None
    estimate_notice: str


class QueueStatePublic(BaseModel):
    doctor_id: str
    department_id: str
    queue_date: str
    current_token: str | None
    current_status: TokenStatus | None
    queue_length: int
    updated_at: datetime


class DoctorStatusUpdate(BaseModel):
    status: DoctorStatus


class TokenActionRequest(BaseModel):
    token_id: str


class NotificationPublic(BaseModel):
    id: str
    token_id: str | None = None
    type: str
    message: str
    is_read: bool
    created_at: datetime
