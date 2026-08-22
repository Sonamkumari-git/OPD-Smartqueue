"""Native MongoDB repositories for user, catalog, queue, and clinical records."""
from datetime import datetime
from typing import Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from app.database.mongodb import get_database


class UserRepository:
    @property
    def collection(self):
        return get_database().users

    async def get_by_email(self, email: str) -> dict | None:
        return await self.collection.find_one({"email": email.lower()})

    async def get_by_id(self, user_id: ObjectId) -> dict | None:
        return await self.collection.find_one({"_id": user_id})

    async def create(self, document: dict) -> dict:
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document


class CatalogRepository:
    @property
    def db(self):
        return get_database()

    async def get_department(self, department_id: ObjectId) -> dict | None:
        return await self.db.departments.find_one({"_id": department_id, "is_active": True})

    async def list_departments(self) -> list[dict]:
        return await self.db.departments.find({"is_active": True}).sort("name", ASCENDING).to_list(length=200)

    async def get_doctor(self, doctor_id: ObjectId) -> dict | None:
        return await self.db.doctors.find_one({"_id": doctor_id})

    async def get_doctor_by_user_id(self, user_id: ObjectId) -> dict | None:
        return await self.db.doctors.find_one({"user_id": user_id})

    async def get_patient_by_user_id(self, user_id: ObjectId) -> dict | None:
        return await self.db.patients.find_one({"user_id": user_id})

    async def list_doctors(self, department_id: ObjectId | None = None) -> list[dict]:
        query: dict[str, Any] = {"status": {"$ne": "OFFLINE"}}
        if department_id:
            query["department_id"] = department_id
        return await self.db.doctors.find(query).sort("created_at", ASCENDING).to_list(length=200)

    async def get_users_by_ids(self, ids: list[ObjectId]) -> dict[ObjectId, dict]:
        documents = await self.db.users.find({"_id": {"$in": ids}}).to_list(length=len(ids))
        return {document["_id"]: document for document in documents}

    async def update_doctor_status(self, doctor_id: ObjectId, status: str) -> dict | None:
        return await self.db.doctors.find_one_and_update({"_id": doctor_id}, {"$set": {"status": status, "updated_at": datetime.now().astimezone()}}, return_document=ReturnDocument.AFTER)


class QueueRepository:
    @property
    def db(self):
        return get_database()

    async def next_sequence(self, department_id: ObjectId, queue_date: str) -> int:
        counter_id = f"{department_id}_{queue_date}"
        document = await self.db.counters.find_one_and_update({"_id": counter_id}, {"$inc": {"sequence": 1}, "$setOnInsert": {"department_id": department_id, "date": queue_date}}, upsert=True, return_document=ReturnDocument.AFTER)
        return int(document["sequence"])

    async def create_token(self, document: dict) -> dict:
        result = await self.db.tokens.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def get_token(self, token_id: ObjectId) -> dict | None:
        return await self.db.tokens.find_one({"_id": token_id})

    async def get_active_token_for_patient(self, patient_id: ObjectId, queue_date: str) -> dict | None:
        return await self.db.tokens.find_one({"patient_id": patient_id, "queue_date": queue_date, "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}})

    async def ordered_active_tokens(self, doctor_id: ObjectId, queue_date: str) -> list[dict]:
        return await self.db.tokens.find({"doctor_id": doctor_id, "queue_date": queue_date, "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}).sort([("priority_rank", ASCENDING), ("created_at", ASCENDING)]).to_list(length=1000)

    async def list_patient_tokens(self, patient_id: ObjectId) -> list[dict]:
        return await self.db.tokens.find({"patient_id": patient_id}).sort("created_at", DESCENDING).to_list(length=100)

    async def list_waiting_visits(self, queue_date: str) -> list[dict]:
        return await self.db.tokens.aggregate([
            {"$match": {"queue_date": queue_date, "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}},
            {"$lookup": {"from": "patients", "localField": "patient_id", "foreignField": "_id", "as": "patient"}},
            {"$unwind": "$patient"},
            {"$lookup": {"from": "users", "localField": "patient.user_id", "foreignField": "_id", "as": "patient_user"}},
            {"$unwind": "$patient_user"},
            {"$project": {"token_number": 1, "status": 1, "patient_id": 1, "doctor_id": 1, "department_id": 1, "created_at": 1, "patient_name": "$patient_user.name"}},
            {"$sort": {"created_at": 1}},
        ]).to_list(length=500)

    async def doctor_has_patient(self, doctor_id: ObjectId, patient_id: ObjectId) -> bool:
        return await self.db.tokens.find_one({"doctor_id": doctor_id, "patient_id": patient_id}) is not None

    async def patient_is_active_today(self, patient_id: ObjectId, queue_date: str) -> bool:
        return await self.db.tokens.find_one({"patient_id": patient_id, "queue_date": queue_date, "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}) is not None

    async def atomically_transition(self, token_id: ObjectId, doctor_id: ObjectId, expected_statuses: list[str], next_status: str, fields: dict) -> dict | None:
        return await self.db.tokens.find_one_and_update({"_id": token_id, "doctor_id": doctor_id, "status": {"$in": expected_statuses}}, {"$set": {"status": next_status, **fields}}, return_document=ReturnDocument.AFTER)

    async def call_next(self, doctor_id: ObjectId, queue_date: str, now: datetime) -> dict | None:
        candidate = await self.db.tokens.find_one({"doctor_id": doctor_id, "queue_date": queue_date, "status": "WAITING"}, sort=[("priority_rank", ASCENDING), ("created_at", ASCENDING)])
        if candidate is None:
            return None
        return await self.atomically_transition(candidate["_id"], doctor_id, ["WAITING"], "CALLED", {"called_at": now, "updated_at": now})

    async def update_queue_state(self, document: dict) -> dict:
        return await self.db.queue_states.find_one_and_update({"doctor_id": document["doctor_id"], "queue_date": document["queue_date"]}, {"$set": document}, upsert=True, return_document=ReturnDocument.AFTER)

    async def get_queue_state(self, doctor_id: ObjectId, queue_date: str) -> dict | None:
        return await self.db.queue_states.find_one({"doctor_id": doctor_id, "queue_date": queue_date})


class ClinicalRepository:
    @property
    def db(self):
        return get_database()

    async def create_consultation(self, document: dict) -> dict:
        result = await self.db.consultations.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def create_vitals(self, document: dict) -> dict:
        result = await self.db.vitals.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def list_vitals(self, patient_id: ObjectId) -> list[dict]:
        return await self.db.vitals.find({"patient_id": patient_id}).sort("recorded_at", DESCENDING).to_list(length=100)


class NotificationRepository:
    @property
    def db(self):
        return get_database()

    async def create(self, document: dict) -> dict:
        result = await self.db.notifications.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def find_recent_type(self, user_id: ObjectId, token_id: ObjectId, notification_type: str) -> dict | None:
        return await self.db.notifications.find_one({"user_id": user_id, "token_id": token_id, "type": notification_type}, sort=[("created_at", DESCENDING)])

    async def list_for_user(self, user_id: ObjectId) -> list[dict]:
        return await self.db.notifications.find({"user_id": user_id}).sort("created_at", DESCENDING).to_list(length=100)

    async def create_audit_log(self, document: dict) -> None:
        await self.db.audit_logs.insert_one(document)
