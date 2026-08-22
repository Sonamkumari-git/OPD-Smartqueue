"""Patient token issuance and queue position read endpoints."""
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user, require_roles
from app.repositories.core import CatalogRepository, QueueRepository
from app.schemas.common import APIResponse, Priority, Role
from app.schemas.queue import TokenCreateRequest, TokenPriorityUpdate
from app.services.queue_service import QueueService
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/queue", tags=["queue"])
service = QueueService()


@router.post("/token", response_model=APIResponse[dict], status_code=201)
async def create_token(payload: TokenCreateRequest, current_user: dict = Depends(require_roles(Role.PATIENT))):
    token = await service.create_token(current_user, payload)
    return APIResponse(data=serialize_document(token), message="OPD token created.")


@router.post("/token/{token_id}/cancel", response_model=APIResponse[dict])
async def cancel_token(token_id: str, current_user: dict = Depends(require_roles(Role.PATIENT))):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await service.cancel_token(current_user, ObjectId(token_id))
    return APIResponse(data=serialize_document(token), message="OPD token cancelled.")


@router.patch("/token/{token_id}/priority", response_model=APIResponse[dict])
async def change_priority(token_id: str, payload: TokenPriorityUpdate, current_user: dict = Depends(require_roles(Role.DOCTOR, Role.ADMIN))):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await service.set_priority(current_user, ObjectId(token_id), payload.priority)
    return APIResponse(data=serialize_document(token), message="Token priority updated.")


@router.get("/token/{token_id}", response_model=APIResponse[dict])
async def token_detail(token_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await QueueRepository().get_token(ObjectId(token_id))
    if token is None:
        raise NotFoundError("Token not found.")
    await _authorize_token_access(token, current_user)
    return APIResponse(data=serialize_document(token))


@router.get("/token/{token_id}/position", response_model=APIResponse[dict])
async def token_position(token_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await QueueRepository().get_token(ObjectId(token_id))
    if token is None:
        raise NotFoundError("Token not found.")
    await _authorize_token_access(token, current_user)
    return APIResponse(data=await service.position(token))


async def _authorize_token_access(token: dict, current_user: dict) -> None:
    if current_user["role"] == Role.ADMIN.value:
        return
    if current_user["role"] == Role.PATIENT.value:
        if token.get("patient_user_id") != current_user["_id"]:
            raise ForbiddenError()
        return
    if current_user["role"] == Role.DOCTOR.value:
        doctor = await CatalogRepository().get_doctor_by_user_id(current_user["_id"])
        if doctor is None or token.get("doctor_id") != doctor["_id"]:
            raise ForbiddenError()
        return
    if current_user["role"] == Role.NURSE.value:
        if str(token.get("department_id")) not in {str(department_id) for department_id in current_user.get("department_ids", [])}:
            raise ForbiddenError()
        return
    raise ForbiddenError()
