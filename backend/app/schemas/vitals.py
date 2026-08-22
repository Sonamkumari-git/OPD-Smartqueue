"""Workflow-only vital-sign validation; these values are never diagnostic outputs."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class BloodPressure(BaseModel):
    systolic: int = Field(ge=50, le=250)
    diastolic: int = Field(ge=30, le=160)

    @model_validator(mode="after")
    def validate_relation(self) -> "BloodPressure":
        if self.diastolic >= self.systolic:
            raise ValueError("Diastolic pressure must be lower than systolic pressure.")
        return self


class VitalsCreateRequest(BaseModel):
    token_id: str
    temperature: float = Field(ge=30.0, le=113.0, description="Temperature stored in degrees Fahrenheit; Celsius input is normalized.")
    heart_rate: int = Field(ge=20, le=260)
    blood_pressure: BloodPressure
    spo2: int = Field(ge=50, le=100)

    @field_validator("temperature")
    @classmethod
    def normalize_temperature(cls, value: float) -> float:
        if 30.0 <= value <= 45.0:
            return round((value * 9 / 5) + 32, 1)
        if 86.0 <= value <= 113.0:
            return value
        raise ValueError("Temperature must be between 30–45°C or 86–113°F.")


class VitalsPublic(BaseModel):
    id: str
    patient_id: str
    token_id: str
    recorded_by: str
    temperature: float
    heart_rate: int
    blood_pressure: BloodPressure
    spo2: int
    recorded_at: datetime
