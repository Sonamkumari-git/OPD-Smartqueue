"""Check seeded OPD records directly in the configured MongoDB database.

This verifier is read-only. It confirms the cross-collection relations and queue
invariants that protect the real Atlas-backed application after seed and workflow runs.
"""

import asyncio

from app.database.mongodb import close_mongo_connection, connect_to_mongo, get_database


SEED_NAMESPACE = "atlas-e2e-2026"
ACTIVE = ["WAITING", "CALLED", "IN_CONSULTATION"]
CURRENT = ["CALLED", "IN_CONSULTATION"]


async def count_invalid_relationships() -> int:
    db = get_database()
    pipeline = [
        {"$match": {"seed_namespace": SEED_NAMESPACE}},
        {"$lookup": {"from": "patients", "localField": "patient_id", "foreignField": "_id", "as": "patient"}},
        {"$lookup": {"from": "users", "localField": "patient_user_id", "foreignField": "_id", "as": "patient_user"}},
        {"$lookup": {"from": "doctors", "localField": "doctor_id", "foreignField": "_id", "as": "doctor"}},
        {"$lookup": {"from": "departments", "localField": "department_id", "foreignField": "_id", "as": "department"}},
        {"$match": {"$expr": {"$or": [
            {"$eq": [{"$size": "$patient"}, 0]},
            {"$eq": [{"$size": "$patient_user"}, 0]},
            {"$eq": [{"$size": "$doctor"}, 0]},
            {"$eq": [{"$size": "$department"}, 0]},
        ]}}},
        {"$count": "count"},
    ]
    result = await db.tokens.aggregate(pipeline).to_list(length=1)
    return int(result[0]["count"]) if result else 0


async def main() -> None:
    await connect_to_mongo()
    try:
        db = get_database()
        duplicate_active_patients = await db.tokens.aggregate([
            {"$match": {"status": {"$in": ACTIVE}}},
            {"$group": {"_id": {"patient_id": "$patient_id", "queue_date": "$queue_date"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$count": "count"},
        ]).to_list(length=1)
        duplicate_current_doctors = await db.tokens.aggregate([
            {"$match": {"status": {"$in": CURRENT}}},
            {"$group": {"_id": {"doctor_id": "$doctor_id", "queue_date": "$queue_date"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$count": "count"},
        ]).to_list(length=1)

        queue_states = await db.queue_states.find({"seed_namespace": SEED_NAMESPACE}).to_list(length=100)
        inconsistent_states = 0
        for state in queue_states:
            actual_count = await db.tokens.count_documents({"doctor_id": state["doctor_id"], "queue_date": state["queue_date"], "status": {"$in": ACTIVE}})
            if actual_count != state.get("queue_length"):
                inconsistent_states += 1

        results = {
            "seeded_users": await db.users.count_documents({"seed_namespace": SEED_NAMESPACE}),
            "seeded_tokens": await db.tokens.count_documents({"seed_namespace": SEED_NAMESPACE}),
            "seeded_consultations": await db.consultations.count_documents({"seed_namespace": SEED_NAMESPACE}),
            "broken_seeded_token_relationships": await count_invalid_relationships(),
            "duplicate_active_patient_day_records": int(duplicate_active_patients[0]["count"]) if duplicate_active_patients else 0,
            "duplicate_current_doctor_day_records": int(duplicate_current_doctors[0]["count"]) if duplicate_current_doctors else 0,
            "queue_states_with_wrong_length": inconsistent_states,
        }
        print(results)
        if any(results[key] for key in ["broken_seeded_token_relationships", "duplicate_active_patient_day_records", "duplicate_current_doctor_day_records", "queue_states_with_wrong_length"]):
            raise SystemExit("Atlas invariant verification failed.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
