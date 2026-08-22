"""Load a serialized wait-time model once and fall back safely to the rule-based baseline."""
from functools import lru_cache
from pathlib import Path
import joblib
import pandas as pd

MODEL_FILE = Path(__file__).parent / "models" / "wait_time_model.joblib"


@lru_cache
def load_model() -> dict | None:
    if not MODEL_FILE.exists():
        return None
    return joblib.load(MODEL_FILE)


def predict_wait_time(features: dict, baseline_minutes: int) -> dict:
    model_bundle = load_model()
    if model_bundle is None:
        estimate = baseline_minutes
        return {"predicted_wait_minutes": estimate, "prediction_lower": max(0, round(estimate * 0.85)), "prediction_upper": max(0, round(estimate * 1.15) + 1), "model_version": "rule_based_baseline", "prediction_source": "baseline"}
    frame = pd.DataFrame([{column: features.get(column) for column in model_bundle["feature_columns"]}])
    estimate = max(0, round(float(model_bundle["pipeline"].predict(frame)[0])))
    spread = max(5, round(estimate * 0.15))
    return {"predicted_wait_minutes": estimate, "prediction_lower": max(0, estimate - spread), "prediction_upper": estimate + spread, "model_version": model_bundle["model_version"], "prediction_source": "trained_model"}
