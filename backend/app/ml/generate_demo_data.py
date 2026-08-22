"""Generate a labelled synthetic development dataset; never represented as hospital data."""
from pathlib import Path
import numpy as np
import pandas as pd
from app.ml.features import FEATURE_COLUMNS

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "synthetic_opd_wait_times.csv"


def generate_dataset(rows: int = 2200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    departments = np.array(["cardiology", "medicine", "ent"])
    doctors = {"cardiology": ["dr_sharma", "dr_kapoor"], "medicine": ["dr_iqbal", "dr_roy"], "ent": ["dr_sen"]}
    department_duration = {"cardiology": 9.0, "medicine": 7.0, "ent": 6.0}
    records = []
    for _ in range(rows):
        department = str(rng.choice(departments, p=[0.35, 0.45, 0.20]))
        doctor = str(rng.choice(doctors[department]))
        hour = int(rng.integers(8, 17))
        minute = int(rng.integers(0, 60))
        day_of_week = int(rng.integers(0, 6))
        patients_ahead = int(rng.integers(0, 19))
        queue_length = int(patients_ahead + rng.integers(1, 8))
        base_duration = department_duration[department] + (1.0 if doctor in {"dr_sharma", "dr_roy"} else 0.0)
        rush_factor = 1.12 if hour in {10, 11, 12} else 0.96 if hour >= 15 else 1.0
        recent_average = max(3.0, base_duration * rush_factor + rng.normal(0, 0.8))
        today_average = max(3.0, base_duration * rush_factor + rng.normal(0, 1.0))
        doctor_average = base_duration + rng.normal(0, 0.5)
        department_average = department_duration[department] + rng.normal(0, 0.4)
        completed = int(rng.integers(0, 35))
        status = "BUSY" if rng.random() < 0.72 else "AVAILABLE"
        waiting_time = max(0, patients_ahead * (0.40 * recent_average + 0.35 * today_average + 0.25 * doctor_average) + (4 if status == "BUSY" else 0) + rng.normal(0, 5.5))
        records.append({"department_code": department.upper(), "doctor_label": doctor, "hour": hour, "minute": minute, "day_of_week": day_of_week, "patients_ahead": patients_ahead, "queue_length": queue_length, "doctor_average_consultation_duration": round(doctor_average, 2), "department_average_consultation_duration": round(department_average, 2), "recent_consultation_average": round(recent_average, 2), "today_consultation_average": round(today_average, 2), "patients_completed_today": completed, "current_doctor_status": status, "consultation_duration": round(recent_average, 2), "waiting_time_minutes": round(float(waiting_time), 2), "dataset_notice": "Synthetic development data only; not real hospital data."})
    return pd.DataFrame(records)


def write_dataset(rows: int = 2200) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    frame = generate_dataset(rows=rows)
    missing = set(FEATURE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Synthetic dataset is missing required ML features: {sorted(missing)}")
    frame.to_csv(DATA_FILE, index=False)
    return DATA_FILE


if __name__ == "__main__":
    output = write_dataset()
    print(f"Synthetic development dataset written to {output}")
