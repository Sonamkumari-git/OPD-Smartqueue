"""Authenticated wait-time prediction endpoint with stored, versioned inference output."""
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.database.mongodb import get_database
from app.repositories.core import QueueRepository
from app.schemas.common import APIResponse, Role
from app.services.queue_service import QueueService
from app.utils.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/predictions", tags=["waiting-time predictions"])
service = QueueService()


@router.get("/wait-time/{token_id}", response_model=APIResponse[dict])
async def wait_time_prediction(token_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(token_id):
        raise NotFoundError("Token not found.")
    token = await QueueRepository().get_token(ObjectId(token_id))
    if token is None:
        raise NotFoundError("Token not found.")
    if current_user["role"] == Role.PATIENT.value and token.get("patient_user_id") != current_user["_id"]:
        raise ForbiddenError()
    estimate = await service.position(token)
    await get_database().ml_predictions.insert_one({"token_id": token["_id"], "predicted_wait_minutes": estimate["estimated_wait_minutes"], "prediction_lower": estimate["estimate_lower_minutes"], "prediction_upper": estimate["estimate_upper_minutes"], "model_version": estimate["model_version"], "created_at": datetime.now().astimezone()})
    return APIResponse(data=estimate)
