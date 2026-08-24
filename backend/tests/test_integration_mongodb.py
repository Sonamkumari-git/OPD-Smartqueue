"""MongoDB-backed integration and concurrency tests; run with a local Community Server."""
import asyncio
from datetime import datetime
import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.database.indexes import create_indexes
from app.database.mongodb import connect_to_mongo, get_database
from app.ml.features import FEATURE_COLUMNS
from app.ml.prediction_service import predict_wait_time
from app.repositories.core import NotificationRepository
from app.schemas.queue import TokenCreateRequest
from app.services.clinical_service import ClinicalService
from app.services.notification_service import NotificationService
from app.services.queue_service import QueueService
from app.routers.vitals import patient_vitals
from app.schemas.vitals import BloodPressure, VitalsCreateRequest, VitalsUpdateRequest
from app.utils.errors import AppError, ConflictError, ForbiddenError


async def reset_database() -> tuple[object, dict]:
    await connect_to_mongo()
    db = get_database()
    await db.client.drop_database(db.name)
    await create_indexes()
    now = datetime.now().astimezone()
    department = {"_id": ObjectId(), "name": "Test Cardiology", "code": "TC", "description": "Test", "is_active": True, "created_at": now, "updated_at": now}
    doctor_user = {"_id": ObjectId(), "name": "Test Doctor", "email": "doctor@test.local", "password_hash": "not-used", "role": "doctor", "is_active": True, "created_at": now}
    doctor = {"_id": ObjectId(), "user_id": doctor_user["_id"], "department_id": department["_id"], "specialization": "Cardiology", "status": "AVAILABLE", "created_at": now}
    nurse = {"_id": ObjectId(), "name": "Test Nurse", "email": "nurse@test.local", "password_hash": "not-used", "role": "nurse", "department_ids": [department["_id"]], "is_active": True, "created_at": now}
    await db.departments.insert_one(department); await db.users.insert_many([doctor_user, nurse]); await db.doctors.insert_one(doctor)
    return db, {"department": department, "doctor_user": doctor_user, "doctor": doctor, "nurse": nurse}


async def create_patient(db, index: int) -> tuple[dict, dict]:
    now = datetime.now().astimezone()
    user = {"_id": ObjectId(), "name": f"Patient {index}", "email": f"patient{index}@test.local", "password_hash": "not-used", "role": "patient", "is_active": True, "created_at": now}
    patient = {"_id": ObjectId(), "user_id": user["_id"], "date_of_birth": "1990-01-01", "gender": "not_specified", "created_at": now}
    await db.users.insert_one(user); await db.patients.insert_one(patient)
    return user, patient


async def insert_waiting_token(db, fixture: dict, patient_user: dict, patient: dict, sequence: int) -> dict:
    now = datetime.now().astimezone()
    token = {"_id": ObjectId(), "token_number": f"TC-{sequence:03d}", "sequence": sequence, "patient_id": patient["_id"], "patient_user_id": patient_user["_id"], "doctor_id": fixture["doctor"]["_id"], "department_id": fixture["department"]["_id"], "status": "WAITING", "priority": "NORMAL", "priority_rank": 2, "queue_date": QueueService.queue_date(), "created_at": now, "updated_at": now, "called_at": None, "consultation_started_at": None, "completed_at": None}
    await db.tokens.insert_one(token)
    return token


def test_concurrent_patient_token_generation_creates_one_active_token():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1)
        service = QueueService(); payload = TokenCreateRequest(department_id=str(fixture["department"]["_id"]), doctor_id=str(fixture["doctor"]["_id"]))
        results = await asyncio.gather(*[service.create_token(patient_user, payload) for _ in range(8)], return_exceptions=True)
        successes = [result for result in results if isinstance(result, dict)]
        assert len(successes) == 1
        assert await db.tokens.count_documents({"patient_id": patient["_id"], "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}) == 1
        assert all(isinstance(result, (dict, ConflictError)) for result in results)
    asyncio.run(scenario())


def test_concurrent_call_next_claims_only_one_current_patient():
    async def scenario():
        db, fixture = await reset_database(); one_user, one = await create_patient(db, 1); two_user, two = await create_patient(db, 2)
        await insert_waiting_token(db, fixture, one_user, one, 1); await insert_waiting_token(db, fixture, two_user, two, 2)
        results = await asyncio.gather(*[QueueService().call_next(fixture["doctor_user"]) for _ in range(6)], return_exceptions=True)
        assert len([result for result in results if isinstance(result, dict)]) == 1
        assert await db.tokens.count_documents({"doctor_id": fixture["doctor"]["_id"], "queue_date": QueueService.queue_date(), "status": {"$in": ["CALLED", "IN_CONSULTATION"]}}) == 1
        assert all(isinstance(result, (dict, ConflictError, AppError)) for result in results)
    asyncio.run(scenario())


def test_consultation_completion_calculates_duration_with_persisted_timestamps():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1)
        await insert_waiting_token(db, fixture, patient_user, patient, 1)
        service = QueueService()
        called = await service.call_next(fixture["doctor_user"])
        started = await service.transition_current(fixture["doctor_user"], called["_id"], ["CALLED"], "IN_CONSULTATION")
        completed = await service.transition_current(fixture["doctor_user"], started["_id"], ["IN_CONSULTATION"], "COMPLETED")
        assert completed["status"] == "COMPLETED"
        consultation = await db.consultations.find_one({"token_id": started["_id"]})
        assert consultation is not None
        assert consultation["duration_seconds"] >= 0
    asyncio.run(scenario())


def test_called_and_in_consultation_positions_do_not_publish_wait_estimates():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1)
        await insert_waiting_token(db, fixture, patient_user, patient, 1)
        service = QueueService()
        called = await service.call_next(fixture["doctor_user"])
        called_position = await service.position(called)
        assert called_position["patient_guidance"] == "CALLED"
        assert called_position["estimated_wait_minutes"] == 0
        assert called_position["recommended_return_at"] is None
        assert "called" in called_position["estimate_notice"].lower()
        started = await service.transition_current(fixture["doctor_user"], called["_id"], ["CALLED"], "IN_CONSULTATION")
        consultation_position = await service.position(started)
        assert consultation_position["patient_guidance"] == "IN_CONSULTATION"
        assert consultation_position["estimated_wait_minutes"] == 0
        assert consultation_position["recommended_return_at"] is None
        assert "consultation" in consultation_position["estimate_notice"].lower()
    asyncio.run(scenario())


def test_nurse_can_read_vital_history_for_an_assigned_active_visit():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1)
        token = await insert_waiting_token(db, fixture, patient_user, patient, 1)
        clinical = ClinicalService()
        vital = await clinical.record_vitals(fixture["nurse"], VitalsCreateRequest(token_id=str(token["_id"]), temperature=98.7, heart_rate=75, blood_pressure=BloodPressure(systolic=118, diastolic=76), spo2=99))
        updated = await clinical.update_vitals(fixture["nurse"], str(vital["_id"]), VitalsUpdateRequest(temperature=99.1, heart_rate=79, blood_pressure=BloodPressure(systolic=120, diastolic=78), spo2=98))
        assert updated["heart_rate"] == 79
        nurse_response = await patient_vitals(str(patient["_id"]), fixture["nurse"])
        assert len(nurse_response.data) == 1
        assert nurse_response.data[0]["token_id"] == str(token["_id"])
        assert nurse_response.data[0]["patient_name"] == "Patient 1"
        queue = QueueService()
        called = await queue.call_next(fixture["doctor_user"])
        await queue.transition_current(fixture["doctor_user"], called["_id"], ["CALLED"], "IN_CONSULTATION")
        doctor_response = await patient_vitals(str(patient["_id"]), fixture["doctor_user"])
        assert doctor_response.data[0]["id"] == str(vital["_id"])
        await clinical.delete_vitals(fixture["nurse"], str(vital["_id"]))
        assert (await patient_vitals(str(patient["_id"]), fixture["nurse"])).data == []
    asyncio.run(scenario())


def test_notification_dedupe_is_atomic_under_concurrency():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1); token = await insert_waiting_token(db, fixture, patient_user, patient, 1)
        service = NotificationService()
        await asyncio.gather(*[service.notify_patient(patient_user["_id"], token["_id"], patient["_id"], "TOKEN_APPROACHING", "Approaching") for _ in range(10)])
        assert await db.notifications.count_documents({"user_id": patient_user["_id"], "token_id": token["_id"], "type": "TOKEN_APPROACHING"}) == 1
    asyncio.run(scenario())


def test_patient_priority_input_is_not_persisted_and_waiting_token_can_cancel():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1)
        payload = TokenCreateRequest.model_validate({"department_id": str(fixture["department"]["_id"]), "doctor_id": str(fixture["doctor"]["_id"]), "priority": "EMERGENCY"})
        service = QueueService(); token = await service.create_token(patient_user, payload)
        assert token["priority"] == "NORMAL"
        cancelled = await service.cancel_token(patient_user, token["_id"])
        assert cancelled["status"] == "CANCELLED"
        with pytest.raises(ConflictError):
            await service.cancel_token(patient_user, token["_id"])
    asyncio.run(scenario())


def test_nurse_cannot_record_vitals_for_unassigned_department_and_doctor_needs_current_visit():
    async def scenario():
        db, fixture = await reset_database(); patient_user, patient = await create_patient(db, 1); token = await insert_waiting_token(db, fixture, patient_user, patient, 1)
        other_department = {"_id": ObjectId(), "name": "Other", "code": "OT", "is_active": True}; await db.departments.insert_one(other_department)
        other_nurse = {"_id": ObjectId(), "name": "Other Nurse", "email": "other-nurse@test.local", "password_hash": "not-used", "role": "nurse", "department_ids": [other_department["_id"]], "is_active": True}; await db.users.insert_one(other_nurse)
        payload = VitalsCreateRequest(token_id=str(token["_id"]), temperature=98.6, heart_rate=72, blood_pressure=BloodPressure(systolic=120, diastolic=80), spo2=98)
        with pytest.raises(ForbiddenError):
            await ClinicalService().record_vitals(other_nurse, payload)
        created = await ClinicalService().record_vitals(fixture["nurse"], payload)
        assert created["patient_id"] == patient["_id"]
    asyncio.run(scenario())


def test_model_contract_requires_every_live_feature():
    missing = {column: 1 for column in FEATURE_COLUMNS[:-1]}
    with pytest.raises(ValueError):
        predict_wait_time(missing, 7)
