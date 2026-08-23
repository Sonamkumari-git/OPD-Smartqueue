"""Seed a coherent, idempotent OPD SmartQueue test dataset into the configured MongoDB database.

Run only with an explicit password and --apply confirmation:
    python -m scripts.seed_atlas_data --apply --password 'choose-a-test-password'

The script uses the application's existing Motor connection, indexes, schema field names, and
MongoDB relationships. Every inserted record is labelled with ``seed_namespace`` so it can be
identified and refreshed safely without touching unlabelled operational data.
"""

import argparse
import asyncio
from datetime import datetime, timedelta

from app.auth.security import hash_password
from app.database.indexes import create_indexes
from app.database.mongodb import close_mongo_connection, connect_to_mongo, get_database


SEED_NAMESPACE = "atlas-e2e-2026"
TEST_DOMAIN = "opdsmartqueue.example.com"
PRIORITY_RANK = {"EMERGENCY": 0, "HIGH": 1, "NORMAL": 2}

DEPARTMENTS = [
    {"name": "Cardiology", "code": "C", "description": "Cardiology OPD"},
    {"name": "General Medicine", "code": "M", "description": "General Medicine OPD"},
    {"name": "ENT", "code": "E", "description": "Ear, nose, and throat OPD"},
]

STAFF = [
    {"key": "admin", "name": "Test Operations Administrator", "email": f"admin@{TEST_DOMAIN}", "role": "admin"},
    {"key": "doctor_card", "name": "Dr. Aarav Mehta", "email": f"dr.aarav.mehta@{TEST_DOMAIN}", "role": "doctor", "department_code": "C", "specialization": "Cardiology", "license_number": "TEST-CARD-1001"},
    {"key": "doctor_med", "name": "Dr. Sana Iyer", "email": f"dr.sana.iyer@{TEST_DOMAIN}", "role": "doctor", "department_code": "M", "specialization": "General Medicine", "license_number": "TEST-MED-1002"},
    {"key": "doctor_ent", "name": "Dr. Kabir Sen", "email": f"dr.kabir.sen@{TEST_DOMAIN}", "role": "doctor", "department_code": "E", "specialization": "Otolaryngology", "license_number": "TEST-ENT-1003"},
    {"key": "nurse_cardiology", "name": "Nurse Kavya Rao", "email": f"nurse.kavya@{TEST_DOMAIN}", "role": "nurse", "department_codes": ["C"]},
    {"key": "nurse_medical", "name": "Nurse Riya Das", "email": f"nurse.riya@{TEST_DOMAIN}", "role": "nurse", "department_codes": ["M", "E"]},
]

PATIENT_NAMES = [
    "Aditi Sharma", "Vikram Patel", "Meera Nair", "Rohan Gupta", "Nisha Verma", "Arjun Kapoor",
    "Priya Menon", "Kunal Shah", "Ishita Bose", "Dev Malhotra", "Tanvi Joshi", "Harsh Singh",
]


def now() -> datetime:
    return datetime.now().astimezone()


async def upsert_user(*, name: str, email: str, role: str, password_hash: str, extra: dict | None = None) -> dict:
    db = get_database()
    timestamp = now()
    document = {
        "name": name,
        "email": email.lower(),
        "phone": None,
        "password_hash": password_hash,
        "role": role,
        "is_active": True,
        "is_seeded": True,
        "seed_namespace": SEED_NAMESPACE,
        "updated_at": timestamp,
        **(extra or {}),
    }
    await db.users.update_one(
        {"email": email.lower()},
        {"$set": document, "$setOnInsert": {"created_at": timestamp}},
        upsert=True,
    )
    return await db.users.find_one({"email": email.lower()})


async def upsert_departments() -> dict[str, dict]:
    db = get_database()
    timestamp = now()
    for department in DEPARTMENTS:
        await db.departments.update_one(
            {"code": department["code"]},
            {"$set": {**department, "is_active": True, "updated_at": timestamp}, "$setOnInsert": {"created_at": timestamp}},
            upsert=True,
        )
    documents = await db.departments.find({"code": {"$in": [item["code"] for item in DEPARTMENTS]}}).to_list(length=10)
    return {document["code"]: document for document in documents}


async def upsert_staff(password_hash: str, departments: dict[str, dict]) -> tuple[dict[str, dict], dict[str, dict]]:
    db = get_database()
    users: dict[str, dict] = {}
    doctors: dict[str, dict] = {}
    timestamp = now()
    for member in STAFF:
        nurse_departments = [departments[code]["_id"] for code in member.get("department_codes", [])]
        user = await upsert_user(
            name=member["name"],
            email=member["email"],
            role=member["role"],
            password_hash=password_hash,
            extra={"department_ids": nurse_departments} if member["role"] == "nurse" else None,
        )
        users[member["key"]] = user
        if member["role"] == "doctor":
            doctor_document = {
                "user_id": user["_id"],
                "department_id": departments[member["department_code"]]["_id"],
                "specialization": member["specialization"],
                "license_number": member["license_number"],
                "status": "AVAILABLE",
                "is_seeded": True,
                "seed_namespace": SEED_NAMESPACE,
                "updated_at": timestamp,
            }
            await db.doctors.update_one(
                {"user_id": user["_id"]},
                {"$set": doctor_document, "$setOnInsert": {"created_at": timestamp}},
                upsert=True,
            )
            doctors[member["key"]] = await db.doctors.find_one({"user_id": user["_id"]})
    return users, doctors


async def upsert_patients(password_hash: str) -> tuple[list[dict], list[dict]]:
    db = get_database()
    users: list[dict] = []
    profiles: list[dict] = []
    timestamp = now()
    for index, name in enumerate(PATIENT_NAMES, start=1):
        user = await upsert_user(
            name=name,
            email=f"patient{index:02d}@{TEST_DOMAIN}",
            role="patient",
            password_hash=password_hash,
        )
        profile = {
            "user_id": user["_id"],
            "date_of_birth": f"19{80 + (index % 15):02d}-{(index % 12) + 1:02d}-{(index % 27) + 1:02d}",
            "gender": ["female", "male", "not_specified"][index % 3],
            "emergency_contact": None,
            "is_seeded": True,
            "seed_namespace": SEED_NAMESPACE,
            "updated_at": timestamp,
        }
        await db.patients.update_one(
            {"user_id": user["_id"]},
            {"$set": profile, "$setOnInsert": {"created_at": timestamp}},
            upsert=True,
        )
        users.append(user)
        profiles.append(await db.patients.find_one({"user_id": user["_id"]}))
    return users, profiles


async def upsert_today_queue(departments: dict[str, dict], doctors: dict[str, dict], patient_users: list[dict], patients: list[dict]) -> dict[str, dict]:
    db = get_database()
    timestamp = now()
    queue_date = timestamp.date().isoformat()
    # A previous end-to-end run may have left one of our own seed tokens in a
    # CALLED/IN_CONSULTATION state. Normalize only this namespace before the
    # canonical snapshot below assigns its one intended current patient. This
    # keeps the partial unique doctor/current/day invariant valid on reruns and
    # never alters unlabelled operational tokens.
    await db.tokens.update_many(
        {"seed_namespace": SEED_NAMESPACE, "queue_date": queue_date, "status": {"$in": ["CALLED", "IN_CONSULTATION"]}},
        {"$set": {"status": "WAITING", "called_at": None, "consultation_started_at": None, "updated_at": timestamp}},
    )
    queue_specs = [
        ("doctor_card", "C", 0, "IN_CONSULTATION", "NORMAL"),
        ("doctor_card", "C", 1, "WAITING", "HIGH"),
        ("doctor_card", "C", 2, "WAITING", "NORMAL"),
        ("doctor_med", "M", 3, "WAITING", "NORMAL"),
        ("doctor_med", "M", 4, "WAITING", "NORMAL"),
        ("doctor_ent", "E", 5, "WAITING", "NORMAL"),
    ]
    seeded_tokens: dict[str, dict] = {}
    highest_sequence: dict[str, int] = {code: 0 for code in departments}
    current_token_by_doctor: dict[str, dict] = {}

    for sequence, (doctor_key, department_code, patient_index, status, priority) in enumerate(queue_specs, start=1):
        doctor = doctors[doctor_key]
        department = departments[department_code]
        token_key = f"today-{doctor_key}-{patient_index}"
        created_at = timestamp - timedelta(minutes=(len(queue_specs) - sequence + 1) * 7)
        token_document = {
            "token_number": f"{department_code}-{sequence:03d}",
            "sequence": sequence,
            "patient_id": patients[patient_index]["_id"],
            "patient_user_id": patient_users[patient_index]["_id"],
            "doctor_id": doctor["_id"],
            "department_id": department["_id"],
            "status": status,
            "priority": priority,
            "priority_rank": PRIORITY_RANK[priority],
            "queue_date": queue_date,
            "created_at": created_at,
            "updated_at": timestamp,
            "called_at": timestamp - timedelta(minutes=10) if status == "IN_CONSULTATION" else None,
            "consultation_started_at": timestamp - timedelta(minutes=8) if status == "IN_CONSULTATION" else None,
            "completed_at": None,
            "is_seeded": True,
            "seed_namespace": SEED_NAMESPACE,
            "seed_key": token_key,
        }
        await db.tokens.update_one({"seed_namespace": SEED_NAMESPACE, "seed_key": token_key}, {"$set": token_document}, upsert=True)
        token = await db.tokens.find_one({"seed_namespace": SEED_NAMESPACE, "seed_key": token_key})
        seeded_tokens[token_key] = token
        highest_sequence[department_code] = max(highest_sequence[department_code], sequence)
        if status in {"CALLED", "IN_CONSULTATION"}:
            current_token_by_doctor[doctor_key] = token

    for department_code, department in departments.items():
        await db.counters.update_one(
            {"_id": f"{department['_id']}_{queue_date}"},
            {"$set": {"department_id": department["_id"], "date": queue_date, "is_seeded": True, "seed_namespace": SEED_NAMESPACE, "updated_at": timestamp}, "$max": {"sequence": highest_sequence[department_code]}},
            upsert=True,
        )

    for doctor_key, doctor in doctors.items():
        department_code = next(spec[1] for spec in queue_specs if spec[0] == doctor_key)
        active_count = sum(1 for token in seeded_tokens.values() if token["doctor_id"] == doctor["_id"] and token["status"] in {"WAITING", "CALLED", "IN_CONSULTATION"})
        current = current_token_by_doctor.get(doctor_key)
        await db.queue_states.update_one(
            {"doctor_id": doctor["_id"], "queue_date": queue_date},
            {"$set": {"doctor_id": doctor["_id"], "department_id": departments[department_code]["_id"], "queue_date": queue_date, "current_token": current["token_number"] if current else None, "current_status": current["status"] if current else None, "queue_length": active_count, "updated_at": timestamp, "is_seeded": True, "seed_namespace": SEED_NAMESPACE}},
            upsert=True,
        )
    return seeded_tokens


async def upsert_clinical_history(staff_users: dict[str, dict], doctors: dict[str, dict], patient_users: list[dict], patients: list[dict], active_tokens: dict[str, dict]) -> None:
    db = get_database()
    timestamp = now()
    doctor_keys = list(doctors)
    for index in range(18):
        doctor_key = doctor_keys[index % len(doctor_keys)]
        patient_index = 6 + (index % (len(patients) - 6))
        ended_at = timestamp - timedelta(days=(index // 3) + 1, minutes=20 + index * 11)
        started_at = ended_at - timedelta(minutes=8 + (index % 6))
        key = f"history-{index:02d}"
        await db.consultations.update_one(
            {"seed_namespace": SEED_NAMESPACE, "seed_key": key},
            {"$set": {"token_id": None, "patient_id": patients[patient_index]["_id"], "doctor_id": doctors[doctor_key]["_id"], "started_at": started_at, "ended_at": ended_at, "duration_seconds": int((ended_at - started_at).total_seconds()), "created_at": ended_at, "is_seeded": True, "seed_namespace": SEED_NAMESPACE, "seed_key": key}},
            upsert=True,
        )

    current = active_tokens["today-doctor_card-0"]
    await db.vitals.update_one(
        {"seed_namespace": SEED_NAMESPACE, "seed_key": "active-cardiology-vitals"},
            {"$set": {"token_id": current["_id"], "patient_id": current["patient_id"], "recorded_by": staff_users["nurse_cardiology"]["_id"], "temperature": 98.4, "heart_rate": 74, "blood_pressure": {"systolic": 118, "diastolic": 76}, "spo2": 99, "recorded_at": timestamp - timedelta(minutes=3), "is_seeded": True, "seed_namespace": SEED_NAMESPACE, "seed_key": "active-cardiology-vitals"}},
        upsert=True,
    )

    for token_key, token in active_tokens.items():
        if token["status"] != "WAITING":
            continue
        await db.notifications.update_one(
            {"dedupe_key": f"{SEED_NAMESPACE}:{token_key}:approaching"},
            {"$set": {"user_id": token["patient_user_id"], "token_id": token["_id"], "type": "TOKEN_APPROACHING", "message": f"Your token {token['token_number']} is active in the queue.", "is_read": False, "dedupe_key": f"{SEED_NAMESPACE}:{token_key}:approaching", "created_at": timestamp, "is_seeded": True, "seed_namespace": SEED_NAMESPACE}},
            upsert=True,
        )
    await db.audit_logs.update_one(
        {"seed_namespace": SEED_NAMESPACE, "seed_key": "seed-complete"},
        {"$set": {"user_id": patient_users[0]["_id"], "action": "ATLAS_SEED_COMPLETED", "entity_type": "seed", "entity_id": SEED_NAMESPACE, "metadata": {"active_tokens": len(active_tokens), "patients": len(patients)}, "timestamp": timestamp, "seed_namespace": SEED_NAMESPACE, "seed_key": "seed-complete"}},
        upsert=True,
    )


async def seed(password: str) -> None:
    await connect_to_mongo()
    try:
        await create_indexes()
        departments = await upsert_departments()
        password_hash = hash_password(password)
        staff_users, doctors = await upsert_staff(password_hash, departments)
        patient_users, patients = await upsert_patients(password_hash)
        active_tokens = await upsert_today_queue(departments, doctors, patient_users, patients)
        await upsert_clinical_history(staff_users, doctors, patient_users, patients, active_tokens)
        db = get_database()
        summary = {
            "departments": await db.departments.count_documents({"code": {"$in": [item["code"] for item in DEPARTMENTS]}}),
            "seeded_users": await db.users.count_documents({"seed_namespace": SEED_NAMESPACE}),
            "seeded_active_tokens": await db.tokens.count_documents({"seed_namespace": SEED_NAMESPACE, "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}),
            "seeded_consultations": await db.consultations.count_documents({"seed_namespace": SEED_NAMESPACE}),
        }
        print(f"Atlas seed completed safely for namespace '{SEED_NAMESPACE}': {summary}")
        print(f"Test account domain: @{TEST_DOMAIN}. Use the password supplied to this command.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the configured MongoDB database with schema-compatible OPD test data.")
    parser.add_argument("--apply", action="store_true", help="Required confirmation before any database write occurs.")
    parser.add_argument("--password", help="Password assigned to the seeded test accounts; do not commit it to source control.")
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit("Refusing to write. Re-run with --apply after reviewing the configured database target.")
    if not args.password or len(args.password) < 8:
        raise SystemExit("Provide a non-empty test password of at least 8 characters via --password.")
    asyncio.run(seed(args.password))
