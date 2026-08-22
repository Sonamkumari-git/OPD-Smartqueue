"""Workflow-only vital-sign validation; these values are never diagnostic outputs."""
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


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
    temperature: float = Field(ge=30.0, le=45.0)
    heart_rate: int = Field(ge=20, le=260)
    blood_pressure: BloodPressure
    spo2: int = Field(ge=50, le=100)


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
