"""MongoDB aggregation-based queue and consultation analytics."""
from datetime import datetime, time, timedelta
from bson import ObjectId
from app.database.mongodb import get_database


class AnalyticsService:
    async def expected_consultation_minutes(self, doctor_id: ObjectId, department_id: ObjectId) -> int:
        db = get_database()
        today_start = datetime.combine(datetime.now().date(), time.min).astimezone()
        pipelines = [
            [{"$match": {"doctor_id": doctor_id, "duration_seconds": {"$gt": 0}, "created_at": {"$gte": today_start}}}, {"$group": {"_id": None, "avg": {"$avg": "$duration_seconds"}}}],
            [{"$match": {"doctor_id": doctor_id, "duration_seconds": {"$gt": 0}}}, {"$sort": {"created_at": -1}}, {"$limit": 30}, {"$group": {"_id": None, "avg": {"$avg": "$duration_seconds"}}}],
            [{"$match": {"duration_seconds": {"$gt": 0}}}, {"$lookup": {"from": "doctors", "localField": "doctor_id", "foreignField": "_id", "as": "doctor"}}, {"$unwind": "$doctor"}, {"$match": {"doctor.department_id": department_id}}, {"$group": {"_id": None, "avg": {"$avg": "$duration_seconds"}}}],
        ]
        values: list[float] = []
        for pipeline in pipelines:
            rows = await db.consultations.aggregate(pipeline).to_list(length=1)
            if rows and rows[0].get("avg"):
                values.append(float(rows[0]["avg"]) / 60)
        return max(2, min(30, round(sum(values) / len(values)))) if values else 7

    async def overview(self, queue_date: str) -> dict:
        db = get_database()
        status_counts = await db.tokens.aggregate([
            {"$match": {"queue_date": queue_date}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]).to_list(length=20)
        counts = {row["_id"]: row["count"] for row in status_counts}
        consultation_stats = await db.consultations.aggregate([
            {"$match": {"created_at": {"$gte": datetime.now().astimezone() - timedelta(days=1)}}},
            {"$group": {"_id": None, "avg_seconds": {"$avg": "$duration_seconds"}, "completed": {"$sum": 1}}},
        ]).to_list(length=1)
        active_doctors = await db.doctors.count_documents({"status": {"$in": ["AVAILABLE", "BUSY", "ON_BREAK"]}})
        return {
            "total_patients_today": sum(counts.values()),
            "patients_waiting": counts.get("WAITING", 0),
            "consultations_completed": counts.get("COMPLETED", 0),
            "skipped_tokens": counts.get("SKIPPED", 0),
            "active_doctors": active_doctors,
            "average_consultation_minutes": round((consultation_stats[0].get("avg_seconds") or 0) / 60, 1) if consultation_stats else 0,
        }

    async def department_load(self, queue_date: str) -> list[dict]:
        db = get_database()
        return await db.tokens.aggregate([
            {"$match": {"queue_date": queue_date}},
            {"$group": {"_id": "$department_id", "total_tokens": {"$sum": 1}, "waiting": {"$sum": {"$cond": [{"$eq": ["$status", "WAITING"]}, 1, 0]}}, "completed": {"$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}}}},
            {"$lookup": {"from": "departments", "localField": "_id", "foreignField": "_id", "as": "department"}},
            {"$unwind": "$department"},
            {"$project": {"_id": 0, "department_id": {"$toString": "$_id"}, "department": "$department.name", "total_tokens": 1, "waiting": 1, "completed": 1}},
            {"$sort": {"total_tokens": -1}},
        ]).to_list(length=50)

    async def doctor_workload(self, queue_date: str) -> list[dict]:
        db = get_database()
        return await db.tokens.aggregate([
            {"$match": {"queue_date": queue_date}},
            {"$group": {"_id": "$doctor_id", "total_tokens": {"$sum": 1}, "waiting": {"$sum": {"$cond": [{"$eq": ["$status", "WAITING"]}, 1, 0]}}, "completed": {"$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}}}},
            {"$lookup": {"from": "doctors", "localField": "_id", "foreignField": "_id", "as": "doctor"}},
            {"$unwind": "$doctor"},
            {"$lookup": {"from": "users", "localField": "doctor.user_id", "foreignField": "_id", "as": "user"}},
            {"$unwind": "$user"},
            {"$project": {"_id": 0, "doctor_id": {"$toString": "$_id"}, "doctor": "$user.name", "total_tokens": 1, "waiting": 1, "completed": 1}},
            {"$sort": {"total_tokens": -1}},
        ]).to_list(length=100)

    async def hourly_load(self, queue_date: str) -> list[dict]:
        db = get_database()
        return await db.tokens.aggregate([
            {"$match": {"queue_date": queue_date}},
            {"$project": {"hour": {"$hour": "$created_at"}}},
            {"$group": {"_id": "$hour", "patients": {"$sum": 1}}},
            {"$project": {"_id": 0, "hour": "$_id", "patients": 1}},
            {"$sort": {"hour": 1}},
        ]).to_list(length=24)
