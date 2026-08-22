"""Patient token issuance and queue position read endpoints."""
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user, require_roles
from app.repositories.core import QueueRepository
from app.schemas.common import APIResponse, Role
from app.schemas.queue import TokenCreateRequest
from app.services.queue_service import QueueService
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/queue", tags=["queue"])
service = QueueService()


@router.post("/token", response_model=APIResponse[dict], status_code=201)
async def create_token(payload: TokenCreateRequest, current_user: dict = Depends(require_roles(Role.PATIENT))):
    token = await service.create_token(current_user, payload)
    return APIResponse(data=serialize_document(token), message="OPD token created.")


@router.get("/token/{token_id}", response_model=APIResponse[dict])
async def token_detail(token_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await QueueRepository().get_token(ObjectId(token_id))
    if token is None:
        raise NotFoundError("Token not found.")
    if current_user["role"] == Role.PATIENT.value and token.get("patient_user_id") != current_user["_id"]:
        raise ForbiddenError()
    return APIResponse(data=serialize_document(token))


@router.get("/token/{token_id}/position", response_model=APIResponse[dict])
async def token_position(token_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await QueueRepository().get_token(ObjectId(token_id))
    if token is None:
        raise NotFoundError("Token not found.")
    if current_user["role"] == Role.PATIENT.value and token.get("patient_user_id") != current_user["_id"]:
        raise ForbiddenError()
    return APIResponse(data=await service.position(token))
