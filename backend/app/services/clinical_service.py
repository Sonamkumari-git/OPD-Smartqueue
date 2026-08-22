"""Nurse workflow vitals service; explicitly not a diagnostic or treatment component."""
from datetime import datetime
from bson import ObjectId
from app.repositories.core import ClinicalRepository, QueueRepository
from app.schemas.vitals import VitalsCreateRequest
from app.services.notification_service import NotificationService
from app.utils.errors import NotFoundError


class ClinicalService:
    def __init__(self) -> None:
        self.clinical = ClinicalRepository()
        self.queue = QueueRepository()
        self.notifications = NotificationService()

    async def record_vitals(self, nurse_user: dict, payload: VitalsCreateRequest) -> dict:
        token = await self.queue.get_token(ObjectId(payload.token_id))
        if token is None:
            raise NotFoundError("Visit token not found.")
        allowed_departments = nurse_user.get("department_ids", [])
        if str(token["department_id"]) not in {str(department_id) for department_id in allowed_departments}:
            from app.utils.errors import ForbiddenError
            raise ForbiddenError("You are not assigned to the department for this visit.")
        if token["status"] not in {"WAITING", "CALLED", "IN_CONSULTATION"}:
            from app.utils.errors import ConflictError
            raise ConflictError("Vitals can be recorded only for an active visit.")
        now = datetime.now().astimezone()
        vital = await self.clinical.create_vitals({"patient_id": token["patient_id"], "token_id": token["_id"], "recorded_by": nurse_user["_id"], "temperature": payload.temperature, "heart_rate": payload.heart_rate, "blood_pressure": payload.blood_pressure.model_dump(), "spo2": payload.spo2, "recorded_at": now})
        await self.notifications.audit(nurse_user["_id"], "RECORD_VITALS", "vitals", vital["_id"], {"token_number": token["token_number"]})
        return vital

    async def patient_vitals(self, patient_id: ObjectId) -> list[dict]:
        return await self.clinical.list_vitals(patient_id)
