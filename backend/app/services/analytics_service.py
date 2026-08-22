"""MongoDB aggregation-based queue, wait-time, consultation, and workload analytics."""
from datetime import datetime, time
from bson import ObjectId
from app.database.mongodb import get_database
from app.config import get_settings


class AnalyticsService:
    def token_match(self, queue_date: str, department_id: ObjectId | None = None, doctor_id: ObjectId | None = None) -> dict:
        match: dict = {"queue_date": queue_date}
        if department_id is not None:
            match["department_id"] = department_id
        if doctor_id is not None:
            match["doctor_id"] = doctor_id
        return match

    async def consultation_feature_profile(self, doctor_id: ObjectId, department_id: ObjectId, queue_date: str) -> dict:
        db = get_database()
        today_start = datetime.combine(datetime.fromisoformat(queue_date).date(), time.min).astimezone()
        doctor_today = await db.consultations.aggregate([
            {"$match": {"doctor_id": doctor_id, "duration_seconds": {"$gt": 0}, "created_at": {"$gte": today_start}}},
            {"$group": {"_id": None, "average": {"$avg": "$duration_seconds"}, "completed": {"$sum": 1}}},
        ]).to_list(length=1)
        recent_doctor = await db.consultations.aggregate([
            {"$match": {"doctor_id": doctor_id, "duration_seconds": {"$gt": 0}}},
            {"$sort": {"created_at": -1}}, {"$limit": 30},
            {"$group": {"_id": None, "average": {"$avg": "$duration_seconds"}}},
        ]).to_list(length=1)
        department_history = await db.consultations.aggregate([
            {"$match": {"duration_seconds": {"$gt": 0}}},
            {"$lookup": {"from": "doctors", "localField": "doctor_id", "foreignField": "_id", "as": "doctor"}}, {"$unwind": "$doctor"},
            {"$match": {"doctor.department_id": department_id}}, {"$group": {"_id": None, "average": {"$avg": "$duration_seconds"}}},
        ]).to_list(length=1)
        def minutes(rows: list[dict], fallback: float = 7.0) -> float:
            return round(float(rows[0].get("average", fallback * 60)) / 60, 2) if rows else fallback
        today_average = minutes(doctor_today)
        recent_average = minutes(recent_doctor)
        department_average = minutes(department_history)
        doctor_average = round((today_average + recent_average) / 2, 2)
        return {"doctor_average_consultation_duration": doctor_average, "department_average_consultation_duration": department_average, "recent_consultation_average": recent_average, "today_consultation_average": today_average, "patients_completed_today": doctor_today[0].get("completed", 0) if doctor_today else 0}

    async def expected_consultation_minutes(self, doctor_id: ObjectId, department_id: ObjectId, queue_date: str | None = None) -> int:
        profile = await self.consultation_feature_profile(doctor_id, department_id, queue_date or datetime.now().date().isoformat())
        settings = get_settings()
        historical = (profile["doctor_average_consultation_duration"] + profile["department_average_consultation_duration"]) / 2
        weighted = (profile["recent_consultation_average"] * settings.baseline_recent_weight) + (profile["today_consultation_average"] * settings.baseline_today_weight) + (historical * settings.baseline_historical_weight)
        return max(2, min(30, round(weighted)))

    async def overview(self, queue_date: str, department_id: ObjectId | None = None, doctor_id: ObjectId | None = None) -> dict:
        db = get_database()
        match = self.token_match(queue_date, department_id, doctor_id)
        counts = await db.tokens.aggregate([
            {"$match": match}, {"$group": {"_id": "$status", "count": {"$sum": 1}, "patients": {"$addToSet": "$patient_id"}}},
        ]).to_list(length=20)
        count_map = {row["_id"]: row["count"] for row in counts}
        total_patients = len({patient for row in counts for patient in row.get("patients", [])})
        wait_stats = await db.tokens.aggregate([
            {"$match": {**match, "called_at": {"$ne": None}}},
            {"$project": {"wait_minutes": {"$divide": [{"$subtract": ["$called_at", "$created_at"]}, 60000]}}},
            {"$group": {"_id": None, "average": {"$avg": "$wait_minutes"}, "maximum": {"$max": "$wait_minutes"}}},
        ]).to_list(length=1)
        consultation_match: dict = {"created_at": {"$gte": datetime.combine(datetime.fromisoformat(queue_date).date(), time.min).astimezone()}}
        if doctor_id is not None:
            consultation_match["doctor_id"] = doctor_id
        consultation_stats = await db.consultations.aggregate([
            {"$match": consultation_match}, {"$group": {"_id": None, "average_seconds": {"$avg": "$duration_seconds"}}},
        ]).to_list(length=1)
        doctor_match: dict = {"status": {"$in": ["AVAILABLE", "BUSY", "ON_BREAK"]}}
        if department_id is not None:
            doctor_match["department_id"] = department_id
        if doctor_id is not None:
            doctor_match["_id"] = doctor_id
        waits = wait_stats[0] if wait_stats else {}
        return {"total_tokens": sum(count_map.values()), "total_patients": total_patients, "patients_waiting": count_map.get("WAITING", 0), "patients_in_service": count_map.get("CALLED", 0) + count_map.get("IN_CONSULTATION", 0), "consultations_completed": count_map.get("COMPLETED", 0), "skipped_tokens": count_map.get("SKIPPED", 0), "cancelled_tokens": count_map.get("CANCELLED", 0), "active_doctors": await db.doctors.count_documents(doctor_match), "average_wait_minutes": round(float(waits.get("average", 0)), 1), "maximum_wait_minutes": round(float(waits.get("maximum", 0)), 1), "average_consultation_minutes": round(float((consultation_stats[0].get("average_seconds") if consultation_stats else 0) or 0) / 60, 1)}

    async def department_load(self, queue_date: str, doctor_id: ObjectId | None = None) -> list[dict]:
        db = get_database()
        match = self.token_match(queue_date, doctor_id=doctor_id)
        return await db.tokens.aggregate([
            {"$match": match}, {"$group": {"_id": "$department_id", "total_tokens": {"$sum": 1}, "waiting": {"$sum": {"$cond": [{"$eq": ["$status", "WAITING"]}, 1, 0]}}, "completed": {"$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}}}},
            {"$lookup": {"from": "departments", "localField": "_id", "foreignField": "_id", "as": "department"}}, {"$unwind": "$department"},
            {"$project": {"_id": 0, "department_id": {"$toString": "$_id"}, "department": "$department.name", "total_tokens": 1, "waiting": 1, "completed": 1}}, {"$sort": {"total_tokens": -1}},
        ]).to_list(length=50)

    async def doctor_workload(self, queue_date: str, department_id: ObjectId | None = None) -> list[dict]:
        db = get_database()
        match = self.token_match(queue_date, department_id=department_id)
        return await db.tokens.aggregate([
            {"$match": match}, {"$group": {"_id": "$doctor_id", "total_tokens": {"$sum": 1}, "waiting": {"$sum": {"$cond": [{"$eq": ["$status", "WAITING"]}, 1, 0]}}, "completed": {"$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}}}},
            {"$lookup": {"from": "doctors", "localField": "_id", "foreignField": "_id", "as": "doctor"}}, {"$unwind": "$doctor"},
            {"$lookup": {"from": "users", "localField": "doctor.user_id", "foreignField": "_id", "as": "user"}}, {"$unwind": "$user"},
            {"$project": {"_id": 0, "doctor_id": {"$toString": "$_id"}, "doctor": "$user.name", "total_tokens": 1, "waiting": 1, "completed": 1}}, {"$sort": {"total_tokens": -1}},
        ]).to_list(length=100)

    async def trends(self, queue_date: str, department_id: ObjectId | None = None, doctor_id: ObjectId | None = None) -> dict:
        db = get_database()
        match = self.token_match(queue_date, department_id, doctor_id)
        arrivals = await db.tokens.aggregate([
            {"$match": match}, {"$project": {"hour": {"$hour": "$created_at"}}}, {"$group": {"_id": "$hour", "patients": {"$sum": 1}}}, {"$project": {"_id": 0, "hour": "$_id", "patients": 1}}, {"$sort": {"hour": 1}},
        ]).to_list(length=24)
        waits = await db.tokens.aggregate([
            {"$match": {**match, "called_at": {"$ne": None}}}, {"$project": {"hour": {"$hour": "$called_at"}, "wait_minutes": {"$divide": [{"$subtract": ["$called_at", "$created_at"]}, 60000]}}}, {"$group": {"_id": "$hour", "average_wait_minutes": {"$avg": "$wait_minutes"}}}, {"$project": {"_id": 0, "hour": "$_id", "average_wait_minutes": {"$round": ["$average_wait_minutes", 1]}}}, {"$sort": {"hour": 1}},
        ]).to_list(length=24)
        consultations = await db.consultations.aggregate([
            {"$match": {"created_at": {"$gte": datetime.combine(datetime.fromisoformat(queue_date).date(), time.min).astimezone()}, **({"doctor_id": doctor_id} if doctor_id else {})}}, {"$project": {"hour": {"$hour": "$created_at"}, "duration_minutes": {"$divide": ["$duration_seconds", 60]}}}, {"$group": {"_id": "$hour", "average_consultation_minutes": {"$avg": "$duration_minutes"}}}, {"$project": {"_id": 0, "hour": "$_id", "average_consultation_minutes": {"$round": ["$average_consultation_minutes", 1]}}}, {"$sort": {"hour": 1}},
        ]).to_list(length=24)
        return {"hourly_arrivals": arrivals, "waiting_time_trend": waits, "consultation_duration_trend": consultations}
