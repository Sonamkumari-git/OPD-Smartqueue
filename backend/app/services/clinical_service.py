"""Nurse workflow vitals service; explicitly not a diagnostic or treatment component."""
from datetime import datetime
from bson import ObjectId
from app.repositories.core import ClinicalRepository, QueueRepository
from app.schemas.vitals import VitalsCreateRequest, VitalsUpdateRequest
from app.services.notification_service import NotificationService
from app.utils.errors import ConflictError, ForbiddenError, NotFoundError


class ClinicalService:
    def __init__(self) -> None:
        self.clinical = ClinicalRepository()
        self.queue = QueueRepository()
        self.notifications = NotificationService()

    async def record_vitals(self, nurse_user: dict, payload: VitalsCreateRequest) -> dict:
        token = await self.queue.get_token(ObjectId(payload.token_id))
        if token is None:
            raise NotFoundError("Visit token not found.")
        self._require_nurse_department(nurse_user, token)
        if token["status"] not in {"WAITING", "CALLED", "IN_CONSULTATION"}:
            raise ConflictError("Vitals can be recorded only for an active visit.")
        now = datetime.now().astimezone()
        patient = await self.clinical.db.patients.find_one({"_id": token["patient_id"]})
        patient_user = await self.clinical.db.users.find_one({"_id": patient["user_id"]}) if patient else None
        vital = await self.clinical.create_vitals({"patient_id": token["patient_id"], "patient_name": patient_user.get("name") if patient_user else None, "token_id": token["_id"], "recorded_by": nurse_user["_id"], "temperature": payload.temperature, "heart_rate": payload.heart_rate, "blood_pressure": payload.blood_pressure.model_dump(), "spo2": payload.spo2, "recorded_at": now, "updated_at": now})
        await self.notifications.audit(nurse_user["_id"], "RECORD_VITALS", "vitals", vital["_id"], {"token_number": token["token_number"]})
        return vital

    def _require_nurse_department(self, nurse_user: dict, token: dict) -> None:
        allowed_departments = nurse_user.get("department_ids", [])
        if str(token["department_id"]) not in {str(department_id) for department_id in allowed_departments}:
            raise ForbiddenError("You are not assigned to the department for this visit.")

    async def _editable_vital(self, nurse_user: dict, vital_id: str) -> tuple[dict, dict]:
        if not ObjectId.is_valid(vital_id):
            raise NotFoundError("Vital record not found.")
        vital = await self.clinical.get_vitals(ObjectId(vital_id))
        if vital is None:
            raise NotFoundError("Vital record not found.")
        if vital["recorded_by"] != nurse_user["_id"]:
            raise ForbiddenError("Only the nurse who recorded this observation may edit or delete it.")
        token = await self.queue.get_token(vital["token_id"])
        if token is None:
            raise NotFoundError("Visit token not found.")
        self._require_nurse_department(nurse_user, token)
        if token["status"] not in {"WAITING", "CALLED", "IN_CONSULTATION"}:
            raise ConflictError("Vitals may be edited only while the visit is active.")
        return vital, token

    async def update_vitals(self, nurse_user: dict, vital_id: str, payload: VitalsUpdateRequest) -> dict:
        vital, token = await self._editable_vital(nurse_user, vital_id)
        updated = await self.clinical.update_vitals(vital["_id"], {"temperature": payload.temperature, "heart_rate": payload.heart_rate, "blood_pressure": payload.blood_pressure.model_dump(), "spo2": payload.spo2, "updated_at": datetime.now().astimezone()})
        await self.notifications.audit(nurse_user["_id"], "UPDATE_VITALS", "vitals", vital["_id"], {"token_number": token["token_number"]})
        return updated

    async def delete_vitals(self, nurse_user: dict, vital_id: str) -> None:
        vital, token = await self._editable_vital(nurse_user, vital_id)
        await self.clinical.delete_vitals(vital["_id"])
        await self.notifications.audit(nurse_user["_id"], "DELETE_VITALS", "vitals", vital["_id"], {"token_number": token["token_number"]})

    async def patient_vitals(self, patient_id: ObjectId) -> list[dict]:
        return await self.clinical.list_vitals(patient_id)
