"""Nurse-only visit queue endpoint for workflow vital capture."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.repositories.core import QueueRepository
from app.schemas.common import APIResponse, Role
from app.services.queue_service import QueueService
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/nurse", tags=["nurse workflow"])


@router.get("/queue", response_model=APIResponse[list[dict]])
async def waiting_queue(_: dict = Depends(require_roles(Role.NURSE))):
    records = await QueueRepository().list_waiting_visits(QueueService.queue_date())
    return APIResponse(data=[serialize_document(record) for record in records])
