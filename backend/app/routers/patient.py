"""Authenticated patient profile, token history, and notification routes."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.repositories.core import CatalogRepository, NotificationRepository, QueueRepository
from app.schemas.common import APIResponse, Role
from app.utils.errors import NotFoundError
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/patients", tags=["patients"])


async def current_patient(current_user: dict) -> dict:
    patient = await CatalogRepository().get_patient_by_user_id(current_user["_id"])
    if patient is None:
        raise NotFoundError("Patient profile not found.")
    return patient


@router.get("/me", response_model=APIResponse[dict])
async def patient_me(current_user: dict = Depends(require_roles(Role.PATIENT))):
    patient = await current_patient(current_user)
    payload = serialize_document(patient)
    payload["user"] = {"id": str(current_user["_id"]), "name": current_user["name"], "email": current_user["email"]}
    return APIResponse(data=payload)


@router.get("/me/tokens", response_model=APIResponse[list[dict]])
async def patient_tokens(current_user: dict = Depends(require_roles(Role.PATIENT))):
    patient = await current_patient(current_user)
    return APIResponse(data=[serialize_document(item) for item in await QueueRepository().list_patient_tokens(patient["_id"])])


@router.get("/me/notifications", response_model=APIResponse[list[dict]])
async def patient_notifications(current_user: dict = Depends(require_roles(Role.PATIENT))):
    return APIResponse(data=[serialize_document(item) for item in await NotificationRepository().list_for_user(current_user["_id"])])
