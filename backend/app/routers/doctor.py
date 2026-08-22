"""Doctor queue-control endpoints with role enforcement and guarded state changes."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.repositories.core import CatalogRepository, QueueRepository
from app.schemas.common import APIResponse, Role
from app.schemas.queue import DoctorStatusUpdate, TokenActionRequest
from app.services.queue_service import QueueService
from app.services.notification_service import NotificationService
from app.utils.errors import NotFoundError
from app.utils.serializers import as_object_id, serialize_document
from app.websocket.manager import manager

router = APIRouter(prefix="/api/doctors", tags=["doctor workflow"])
service = QueueService()


@router.get("/me/queue", response_model=APIResponse[list[dict]])
async def doctor_queue(current_user: dict = Depends(require_roles(Role.DOCTOR))):
    doctor = await CatalogRepository().get_doctor_by_user_id(current_user["_id"])
    if doctor is None:
        raise NotFoundError("Doctor profile not found.")
    queue = await QueueRepository().doctor_queue_details(doctor["_id"], service.queue_date())
    return APIResponse(data=[serialize_document(item) for item in queue])


@router.post("/me/call-next", response_model=APIResponse[dict])
async def call_next(current_user: dict = Depends(require_roles(Role.DOCTOR))):
    return APIResponse(data=serialize_document(await service.call_next(current_user)), message="Next patient called.")


@router.post("/me/start-consultation", response_model=APIResponse[dict])
async def start_consultation(payload: TokenActionRequest, current_user: dict = Depends(require_roles(Role.DOCTOR))):
    token = await service.transition_current(current_user, as_object_id(payload.token_id, "token id"), ["CALLED"], "IN_CONSULTATION")
    return APIResponse(data=serialize_document(token), message="Consultation started.")


@router.post("/me/complete-consultation", response_model=APIResponse[dict])
async def complete_consultation(payload: TokenActionRequest, current_user: dict = Depends(require_roles(Role.DOCTOR))):
    token = await service.transition_current(current_user, as_object_id(payload.token_id, "token id"), ["IN_CONSULTATION"], "COMPLETED")
    return APIResponse(data=serialize_document(token), message="Consultation completed.")


@router.post("/me/skip-patient", response_model=APIResponse[dict])
async def skip_patient(payload: TokenActionRequest, current_user: dict = Depends(require_roles(Role.DOCTOR))):
    token = await service.transition_current(current_user, as_object_id(payload.token_id, "token id"), ["CALLED"], "SKIPPED")
    return APIResponse(data=serialize_document(token), message="Patient token skipped.")


@router.patch("/me/status", response_model=APIResponse[dict])
async def set_status(payload: DoctorStatusUpdate, current_user: dict = Depends(require_roles(Role.DOCTOR))):
    doctor = await CatalogRepository().get_doctor_by_user_id(current_user["_id"])
    if doctor is None:
        raise NotFoundError("Doctor profile not found.")
    updated = await CatalogRepository().update_doctor_status(doctor["_id"], payload.status.value)
    await NotificationService().audit(current_user["_id"], "DOCTOR_STATUS_CHANGED", "doctor", doctor["_id"], {"status": payload.status.value})
    event = {"event": "DOCTOR_STATUS_CHANGED", "doctor_id": str(doctor["_id"]), "department_id": str(doctor["department_id"]), "status": payload.status.value}
    await manager.broadcast_to_department(str(doctor["department_id"]), event)
    await manager.broadcast_to_doctor(str(doctor["_id"]), event)
    await service.refresh_and_broadcast(doctor["_id"], doctor["department_id"], service.queue_date())
    return APIResponse(data=serialize_document(updated), message="Doctor status updated.")
