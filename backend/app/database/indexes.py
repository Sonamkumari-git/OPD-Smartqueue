"""MongoDB indexes designed around actual OPD queue query patterns."""
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database


async def create_indexes() -> None:
    db = get_database()
    await db.users.create_index([("email", ASCENDING)], unique=True, name="users_email_unique")
    await db.users.create_index([("role", ASCENDING)], name="users_role")
    await db.departments.create_index([("name", ASCENDING)], unique=True, name="departments_name_unique")
    await db.departments.create_index([("code", ASCENDING)], unique=True, name="departments_code_unique")
    await db.doctors.create_index([("user_id", ASCENDING)], unique=True, name="doctors_user_unique")
    await db.doctors.create_index([("department_id", ASCENDING), ("status", ASCENDING)], name="doctors_department_status")
    await db.patients.create_index([("user_id", ASCENDING)], unique=True, name="patients_user_unique")
    await db.tokens.create_index([("department_id", ASCENDING), ("queue_date", ASCENDING), ("sequence", ASCENDING)], unique=True, name="tokens_department_day_sequence_unique")
    await db.tokens.create_index([("patient_id", ASCENDING), ("queue_date", ASCENDING)], unique=True, partialFilterExpression={"status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}, name="tokens_patient_active_day_unique")
    await db.tokens.create_index([("doctor_id", ASCENDING), ("queue_date", ASCENDING)], unique=True, partialFilterExpression={"status": {"$in": ["CALLED", "IN_CONSULTATION"]}}, name="tokens_doctor_current_day_unique")
    await db.tokens.create_index([("doctor_id", ASCENDING), ("queue_date", ASCENDING), ("status", ASCENDING), ("priority_rank", ASCENDING), ("created_at", ASCENDING)], name="tokens_doctor_live_queue")
    await db.tokens.create_index([("department_id", ASCENDING), ("queue_date", ASCENDING), ("status", ASCENDING)], name="tokens_department_daily_status")
    await db.tokens.create_index([("patient_id", ASCENDING), ("created_at", DESCENDING)], name="tokens_patient_history")
    await db.consultations.create_index([("doctor_id", ASCENDING), ("created_at", DESCENDING)], name="consultations_doctor_history")
    await db.consultations.create_index([("patient_id", ASCENDING), ("created_at", DESCENDING)], name="consultations_patient_history")
    await db.vitals.create_index([("token_id", ASCENDING)], name="vitals_token")
    await db.vitals.create_index([("patient_id", ASCENDING), ("recorded_at", DESCENDING)], name="vitals_patient_history")
    await db.notifications.create_index([("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", DESCENDING)], name="notifications_user_unread")
    await db.notifications.create_index([("dedupe_key", ASCENDING)], unique=True, sparse=True, name="notifications_dedupe_unique")
    await db.queue_states.create_index([("doctor_id", ASCENDING), ("queue_date", ASCENDING)], unique=True, name="queue_state_doctor_day_unique")
    await db.ml_predictions.create_index([("token_id", ASCENDING), ("created_at", DESCENDING)], name="predictions_token_history")
    await db.audit_logs.create_index([("timestamp", DESCENDING)], name="audit_timestamp")
    await db.audit_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="audit_user_history")
    await db.audit_logs.create_index([("action", ASCENDING), ("metadata.email", ASCENDING), ("timestamp", DESCENDING)], name="audit_login_attempts")
