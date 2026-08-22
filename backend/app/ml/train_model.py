"""Train and objectively compare regression models using only synthetic development data."""
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from app.ml.generate_demo_data import DATA_FILE, write_dataset

MODEL_DIR = Path(__file__).parent / "models"
MODEL_FILE = MODEL_DIR / "wait_time_model.joblib"
METRICS_FILE = MODEL_DIR / "wait_time_metrics.json"
TARGET = "waiting_time_minutes"
CATEGORICAL = ["doctor_id", "department_id", "current_doctor_status"]
NUMERIC = ["hour", "minute", "day_of_week", "patients_ahead", "queue_length", "doctor_average_consultation_duration", "department_average_consultation_duration", "recent_consultation_average", "today_consultation_average", "patients_completed_today"]


def train_and_save() -> dict:
    if not DATA_FILE.exists():
        write_dataset()
    frame = pd.read_csv(DATA_FILE)
    features = frame[CATEGORICAL + NUMERIC]
    target = frame[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    preprocessing = ColumnTransformer([("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL), ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), NUMERIC)])
    candidates = {"linear_regression_v1": LinearRegression(), "random_forest_v1": RandomForestRegressor(n_estimators=180, min_samples_leaf=3, random_state=42, n_jobs=-1), "gradient_boosting_v1": GradientBoostingRegressor(n_estimators=180, max_depth=2, learning_rate=0.04, random_state=42)}
    metrics = {}
    trained = {}
    for name, model in candidates.items():
        pipeline = Pipeline([("preprocessing", preprocessing), ("model", model)])
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        metrics[name] = {"mae": round(float(mean_absolute_error(y_test, predictions)), 3), "rmse": round(float(mean_squared_error(y_test, predictions) ** 0.5), 3), "r2": round(float(r2_score(y_test, predictions)), 4)}
        trained[name] = pipeline
    best_name = min(metrics, key=lambda name: metrics[name]["mae"])
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": trained[best_name], "model_version": best_name, "feature_columns": CATEGORICAL + NUMERIC, "dataset_notice": "Synthetic development data only; not real hospital data."}, MODEL_FILE)
    result = {"best_model": best_name, "metrics": metrics, "dataset_notice": "Synthetic development data only; not real hospital data."}
    METRICS_FILE.write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    result = train_and_save()
    print(json.dumps(result, indent=2))
