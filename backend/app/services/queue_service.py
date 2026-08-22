"""Priority-aware FIFO queue orchestration, atomic token issuance, and live event emission."""
from datetime import datetime, timedelta
from bson import ObjectId
from app.config import get_settings
from app.repositories.core import CatalogRepository, QueueRepository
from app.schemas.common import Priority
from app.schemas.queue import TokenCreateRequest
from app.services.analytics_service import AnalyticsService
from app.ml.prediction_service import predict_wait_time
from app.services.notification_service import NotificationService
from app.utils.errors import AppError, ConflictError, NotFoundError
from app.websocket.manager import manager

PRIORITY_RANK = {"EMERGENCY": 0, "HIGH": 1, "NORMAL": 2}
ACTIVE_STATUSES = ["WAITING", "CALLED", "IN_CONSULTATION"]


class QueueService:
    def __init__(self) -> None:
        self.catalog = CatalogRepository()
        self.repository = QueueRepository()
        self.analytics = AnalyticsService()
        self.notifications = NotificationService()
        self.settings = get_settings()

    @staticmethod
    def queue_date() -> str:
        return datetime.now().date().isoformat()

    async def create_token(self, current_user: dict, payload: TokenCreateRequest) -> dict:
        patient = await self.catalog.get_patient_by_user_id(current_user["_id"])
        if patient is None:
            raise NotFoundError("Patient profile not found.")
        department_id = ObjectId(payload.department_id) if ObjectId.is_valid(payload.department_id) else None
        doctor_id = ObjectId(payload.doctor_id) if ObjectId.is_valid(payload.doctor_id) else None
        if not department_id or not doctor_id:
            raise AppError("Invalid department or doctor identifier.", "INVALID_ID", 422)
        department = await self.catalog.get_department(department_id)
        doctor = await self.catalog.get_doctor(doctor_id)
        if department is None or doctor is None or doctor.get("department_id") != department_id:
            raise NotFoundError("The selected doctor is not available in this department.")
        if doctor.get("status") in {"ON_BREAK", "OFFLINE"}:
            raise ConflictError("The selected doctor is currently unavailable.")
        queue_date = self.queue_date()
        if await self.repository.get_active_token_for_patient(patient["_id"], queue_date):
            raise ConflictError("You already have an active OPD token today.")
        now = datetime.now().astimezone()
        sequence = await self.repository.next_sequence(department_id, queue_date)
        token = await self.repository.create_token({
            "token_number": f"{department['code']}-{sequence:03d}", "sequence": sequence,
            "patient_id": patient["_id"], "patient_user_id": current_user["_id"], "doctor_id": doctor_id,
            "department_id": department_id, "status": "WAITING", "priority": payload.priority.value,
            "priority_rank": PRIORITY_RANK[payload.priority.value], "queue_date": queue_date,
            "created_at": now, "updated_at": now, "called_at": None, "consultation_started_at": None, "completed_at": None,
        })
        await self.notifications.audit(current_user["_id"], "CREATE_TOKEN", "token", token["_id"], {"token_number": token["token_number"]})
        await self.notifications.notify_patient(current_user["_id"], token["_id"], patient["_id"], "TOKEN_CREATED", f"Your token {token['token_number']} has been created.")
        await self.refresh_and_broadcast(doctor_id, department_id, queue_date)
        return token

    async def position(self, token: dict) -> dict:
        active = await self.repository.ordered_active_tokens(token["doctor_id"], token["queue_date"])
        index = next((i for i, item in enumerate(active) if item["_id"] == token["_id"]), None)
        doctor = await self.catalog.get_doctor(token["doctor_id"])
        state = await self.repository.get_queue_state(token["doctor_id"], token["queue_date"])
        patients_ahead = sum(1 for item in active[:index] if item["status"] == "WAITING") if index is not None else 0
        expected_minutes = await self.analytics.expected_consultation_minutes(token["doctor_id"], token["department_id"])
        baseline_minutes = patients_ahead * expected_minutes
        current_time = datetime.now().astimezone()
        model_estimate = predict_wait_time({"doctor_id": str(token["doctor_id"]), "department_id": str(token["department_id"]), "hour": current_time.hour, "minute": current_time.minute, "day_of_week": current_time.weekday(), "patients_ahead": patients_ahead, "queue_length": len(active), "doctor_average_consultation_duration": expected_minutes, "department_average_consultation_duration": expected_minutes, "recent_consultation_average": expected_minutes, "today_consultation_average": expected_minutes, "patients_completed_today": 0, "current_doctor_status": doctor.get("status", "OFFLINE") if doctor else "OFFLINE"}, baseline_minutes)
        estimated = model_estimate["predicted_wait_minutes"]
        recommended = current_time + timedelta(minutes=estimated) if token["status"] == "WAITING" else None
        return {"token_id": str(token["_id"]), "token_number": token["token_number"], "position": index + 1 if index is not None else None, "patients_ahead": patients_ahead, "queue_length": len(active), "currently_serving": state.get("current_token") if state else None, "doctor_status": doctor.get("status", "OFFLINE") if doctor else "OFFLINE", "baseline_wait_minutes": baseline_minutes, "estimated_wait_minutes": estimated, "estimate_lower_minutes": model_estimate["prediction_lower"], "estimate_upper_minutes": model_estimate["prediction_upper"], "model_version": model_estimate["model_version"], "prediction_source": model_estimate["prediction_source"], "recommended_return_at": recommended, "estimate_notice": "Waiting time is an estimate and may change with real-time queue conditions."}

    async def refresh_and_broadcast(self, doctor_id: ObjectId, department_id: ObjectId, queue_date: str) -> dict:
        active = await self.repository.ordered_active_tokens(doctor_id, queue_date)
        current = next((item for item in active if item["status"] in {"CALLED", "IN_CONSULTATION"}), None)
        now = datetime.now().astimezone()
        state = await self.repository.update_queue_state({"doctor_id": doctor_id, "department_id": department_id, "queue_date": queue_date, "current_token": current["token_number"] if current else None, "current_status": current["status"] if current else None, "queue_length": len(active), "updated_at": now})
        department_event = {"event": "QUEUE_UPDATED", "doctor_id": str(doctor_id), "department_id": str(department_id), "current_token": state.get("current_token"), "current_status": state.get("current_status"), "queue_length": len(active), "updated_at": now}
        await manager.broadcast_to_department(str(department_id), department_event)
        await manager.broadcast_to_doctor(str(doctor_id), department_event)
        for item in active:
            snapshot = await self.position(item)
            patient_event = {"event": "QUEUE_UPDATED", **snapshot}
            await manager.broadcast_to_patient(str(item["patient_id"]), patient_event)
            if snapshot["patients_ahead"] <= self.settings.approaching_threshold and item["status"] == "WAITING":
                await self.notifications.notify_patient(item.get("patient_user_id"), item["_id"], item["patient_id"], "TOKEN_APPROACHING", f"Your token {item['token_number']} is approaching. {snapshot['patients_ahead']} patient(s) are ahead.")
        return state

    async def call_next(self, doctor_user: dict) -> dict:
        doctor = await self.catalog.get_doctor_by_user_id(doctor_user["_id"])
        if doctor is None:
            raise NotFoundError("Doctor profile not found.")
        if doctor.get("status") in {"ON_BREAK", "OFFLINE"}:
            raise ConflictError("Update your availability before calling a patient.")
        queue_date = self.queue_date()
        active = await self.repository.ordered_active_tokens(doctor["_id"], queue_date)
        if any(item["status"] in {"CALLED", "IN_CONSULTATION"} for item in active):
            raise ConflictError("Complete or skip the current patient before calling the next patient.")
        token = await self.repository.call_next(doctor["_id"], queue_date, datetime.now().astimezone())
        if token is None:
            raise AppError("The queue has no waiting patients.", "QUEUE_EMPTY", 409)
        await self.notifications.audit(doctor_user["_id"], "CALL_NEXT_PATIENT", "token", token["_id"], {"token_number": token["token_number"]})
        await self.notifications.notify_patient(token.get("patient_user_id"), token["_id"], token["patient_id"], "YOUR_TURN", f"Your token {token['token_number']} has been called.")
        await self.refresh_and_broadcast(doctor["_id"], doctor["department_id"], queue_date)
        return token

    async def transition_current(self, doctor_user: dict, token_id: ObjectId, expected: list[str], next_status: str) -> dict:
        doctor = await self.catalog.get_doctor_by_user_id(doctor_user["_id"])
        if doctor is None:
            raise NotFoundError("Doctor profile not found.")
        now = datetime.now().astimezone()
        fields = {"updated_at": now}
        if next_status == "IN_CONSULTATION":
            fields["consultation_started_at"] = now
        if next_status == "COMPLETED":
            fields["completed_at"] = now
        token = await self.repository.atomically_transition(token_id, doctor["_id"], expected, next_status, fields)
        if token is None:
            raise ConflictError("This token is no longer in a state that allows that action.")
        await self.notifications.audit(doctor_user["_id"], f"TOKEN_{next_status}", "token", token["_id"], {"token_number": token["token_number"]})
        if next_status == "COMPLETED":
            duration_seconds = max(0, int((now - token["consultation_started_at"]).total_seconds()))
            from app.repositories.core import ClinicalRepository
            await ClinicalRepository().create_consultation({"token_id": token["_id"], "patient_id": token["patient_id"], "doctor_id": doctor["_id"], "started_at": token["consultation_started_at"], "ended_at": now, "duration_seconds": duration_seconds, "created_at": now})
            await self.notifications.notify_patient(token.get("patient_user_id"), token["_id"], token["patient_id"], "CONSULTATION_COMPLETED", f"Your consultation for token {token['token_number']} has been completed.")
        await self.refresh_and_broadcast(doctor["_id"], doctor["department_id"], token["queue_date"])
        return token
