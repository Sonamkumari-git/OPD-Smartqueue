"""Nurse-recorded workflow vitals endpoints, without diagnosis or treatment logic."""
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.repositories.core import CatalogRepository, QueueRepository
from app.schemas.common import APIResponse, Role
from app.schemas.vitals import VitalsCreateRequest
from app.services.clinical_service import ClinicalService
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/vitals", tags=["vitals workflow"])
service = ClinicalService()


@router.post("", response_model=APIResponse[dict], status_code=201)
async def record_vitals(payload: VitalsCreateRequest, current_user: dict = Depends(require_roles(Role.NURSE))):
    vital = await service.record_vitals(current_user, payload)
    return APIResponse(data=serialize_document(vital), message="Vitals recorded for workflow use.")


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
        if doctor is None or not await queue.doctor_has_patient(doctor["_id"], patient_object_id):
            raise ForbiddenError()
    elif not await queue.patient_is_active_today(patient_object_id, service.queue.queue_date()):
        raise ForbiddenError("Nurses may view vitals only for an active visit.")
    return APIResponse(data=[serialize_document(item) for item in await service.patient_vitals(patient_object_id)])
