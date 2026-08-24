"""Nurse-recorded workflow vitals endpoints, without diagnosis or treatment logic."""
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.repositories.core import CatalogRepository, QueueRepository
from app.schemas.common import APIResponse, Role
from app.schemas.vitals import VitalsCreateRequest, VitalsUpdateRequest
from app.services.clinical_service import ClinicalService
from app.services.queue_service import QueueService
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/vitals", tags=["vitals workflow"])
service = ClinicalService()


@router.post("", response_model=APIResponse[dict], status_code=201)
async def record_vitals(payload: VitalsCreateRequest, current_user: dict = Depends(require_roles(Role.NURSE))):
    vital = await service.record_vitals(current_user, payload)
    return APIResponse(data=serialize_document(vital), message="Vitals recorded for workflow use.")


@router.patch("/{vital_id}", response_model=APIResponse[dict])
async def update_vitals(vital_id: str, payload: VitalsUpdateRequest, current_user: dict = Depends(require_roles(Role.NURSE))):
    vital = await service.update_vitals(current_user, vital_id, payload)
    return APIResponse(data=serialize_document(vital), message="Workflow vital observation updated.")


@router.delete("/{vital_id}", response_model=APIResponse[dict])
async def delete_vitals(vital_id: str, current_user: dict = Depends(require_roles(Role.NURSE))):
    await service.delete_vitals(current_user, vital_id)
    return APIResponse(data={"id": vital_id}, message="Workflow vital observation deleted.")


@router.get("/{patient_id}", response_model=APIResponse[list[dict]])
async def patient_vitals(patient_id: str, current_user: dict = Depends(require_roles(Role.PATIENT, Role.DOCTOR, Role.NURSE))):
    if not ObjectId.is_valid(patient_id):
        raise NotFoundError("Patient profile not found.")
    patient_object_id = ObjectId(patient_id)
    queue = QueueRepository()
    if current_user["role"] == Role.PATIENT.value:
        patient = await CatalogRepository().get_patient_by_user_id(current_user["_id"])
        if patient is None or patient["_id"] != patient_object_id:
            raise ForbiddenError()
    elif current_user["role"] == Role.DOCTOR.value:
        doctor = await CatalogRepository().get_doctor_by_user_id(current_user["_id"])
        if doctor is None or not await queue.doctor_has_active_patient(doctor["_id"], patient_object_id, QueueService.queue_date()):
            raise ForbiddenError()
    else:
        allowed_departments = {str(department_id) for department_id in current_user.get("department_ids", [])}
        visits = await queue.list_waiting_visits(QueueService.queue_date())
        if not any(visit["patient_id"] == patient_object_id and str(visit["department_id"]) in allowed_departments for visit in visits):
            raise ForbiddenError("Nurses may view vitals only for an active visit in an assigned department.")
    return APIResponse(data=[serialize_document(item) for item in await service.patient_vitals(patient_object_id)])
