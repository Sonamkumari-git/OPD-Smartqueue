"""Single source of truth for semantically aligned synthetic training and live inference features."""
CATEGORICAL = ["department_code", "current_doctor_status"]
NUMERIC = [
    "hour", "minute", "day_of_week", "patients_ahead", "queue_length",
    "doctor_average_consultation_duration", "department_average_consultation_duration",
    "recent_consultation_average", "today_consultation_average", "patients_completed_today",
]
FEATURE_COLUMNS = CATEGORICAL + NUMERIC
TARGET = "waiting_time_minutes"


def feature_contract() -> dict:
    return {"categorical": CATEGORICAL, "numeric": NUMERIC, "feature_columns": FEATURE_COLUMNS, "target": TARGET, "units": {"doctor_average_consultation_duration": "minutes", "department_average_consultation_duration": "minutes", "recent_consultation_average": "minutes", "today_consultation_average": "minutes", "waiting_time_minutes": "minutes"}}
