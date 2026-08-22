"""Create clearly labeled, local-only OPD demo records for the end-to-end workflow."""
import asyncio
from datetime import datetime, timedelta
from app.auth.security import hash_password
from app.database.indexes import create_indexes
from app.database.mongodb import close_mongo_connection, connect_to_mongo, get_database
from scripts.init_db import ensure_departments

DEMO_PASSWORD = "DemoPass!123"


async def ensure_user(name: str, email: str, role: str) -> dict:
    db = get_database()
    user = await db.users.find_one({"email": email})
    if user:
        return user
    now = datetime.now().astimezone()
    document = {"name": name, "email": email, "phone": None, "password_hash": hash_password(DEMO_PASSWORD), "role": role, "is_active": True, "is_demo": True, "created_at": now, "updated_at": now}
    result = await db.users.insert_one(document)
    document["_id"] = result.inserted_id
    return document


async def ensure_patient(index: int) -> tuple[dict, dict]:
    db = get_database()
    email = f"patient{index:02d}@opdsmartqueue.local"
    user = await ensure_user(f"Demo Patient {index:02d}", email, "patient")
    patient = await db.patients.find_one({"user_id": user["_id"]})
    if patient:
        return user, patient
    now = datetime.now().astimezone()
    document = {"user_id": user["_id"], "date_of_birth": "1990-01-01", "gender": "not_specified", "emergency_contact": None, "is_demo": True, "created_at": now, "updated_at": now}
    result = await db.patients.insert_one(document)
    document["_id"] = result.inserted_id
    return user, document


async def seed() -> None:
    await connect_to_mongo()
    try:
        await create_indexes()
        await ensure_departments()
        db = get_database()
        now = datetime.now().astimezone()
        queue_date = now.date().isoformat()
        cardiology = await db.departments.find_one({"code": "C"})
        admin = await ensure_user("Demo Administrator", "admin@opdsmartqueue.local", "admin")
        doctor_user = await ensure_user("Dr. Sharma", "dr.sharma@opdsmartqueue.local", "doctor")
        nurse_user = await ensure_user("Nurse Asha", "nurse.asha@opdsmartqueue.local", "nurse")
        doctor = await db.doctors.find_one({"user_id": doctor_user["_id"]})
        if doctor is None:
            doctor_doc = {"user_id": doctor_user["_id"], "department_id": cardiology["_id"], "specialization": "Cardiology", "license_number": "DEMO-CARD-001", "status": "BUSY", "is_demo": True, "created_at": now, "updated_at": now}
            inserted = await db.doctors.insert_one(doctor_doc)
            doctor_doc["_id"] = inserted.inserted_id
            doctor = doctor_doc

        await db.tokens.delete_many({"is_demo": True, "queue_date": queue_date, "doctor_id": doctor["_id"]})
        await db.consultations.delete_many({"is_demo": True})
        patients = [await ensure_patient(index) for index in range(1, 10)]
        demo_patient_user, demo_patient = patients[-1]
        token_numbers = list(range(142, 151))
        token_docs = []
        for offset, number in enumerate(token_numbers):
            user, patient = patients[min(offset, len(patients) - 1)]
            status = "IN_CONSULTATION" if number == 142 else "WAITING"
            created_at = now - timedelta(minutes=(151 - number) * 8)
            token_docs.append({"token_number": f"C-{number:03d}", "sequence": number, "patient_id": patient["_id"], "patient_user_id": user["_id"], "doctor_id": doctor["_id"], "department_id": cardiology["_id"], "status": status, "priority": "NORMAL", "priority_rank": 2, "queue_date": queue_date, "created_at": created_at, "updated_at": now, "called_at": now - timedelta(minutes=5) if number == 142 else None, "consultation_started_at": now - timedelta(minutes=4) if number == 142 else None, "completed_at": None, "is_demo": True})
        await db.tokens.insert_many(token_docs)
        await db.counters.update_one({"_id": f"{cardiology['_id']}_{queue_date}"}, {"$set": {"department_id": cardiology["_id"], "date": queue_date, "sequence": 150, "is_demo": True}}, upsert=True)
        await db.queue_states.update_one({"doctor_id": doctor["_id"], "queue_date": queue_date}, {"$set": {"department_id": cardiology["_id"], "doctor_id": doctor["_id"], "queue_date": queue_date, "current_token": "C-142", "current_status": "IN_CONSULTATION", "queue_length": 9, "updated_at": now, "is_demo": True}}, upsert=True)
        c142 = token_docs[0]
        await db.vitals.delete_many({"token_id": c142.get("_id")})
        for index in range(1, 41):
            ended = now - timedelta(days=(index // 8) + 1, minutes=index * 9)
            await db.consultations.insert_one({"token_id": None, "patient_id": demo_patient["_id"], "doctor_id": doctor["_id"], "started_at": ended - timedelta(minutes=7), "ended_at": ended, "duration_seconds": 420, "created_at": ended, "is_demo": True})
        print("Demo data seeded. Local credentials: admin@opdsmartqueue.local, dr.sharma@opdsmartqueue.local, nurse.asha@opdsmartqueue.local, patient09@opdsmartqueue.local — password: DemoPass!123")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
