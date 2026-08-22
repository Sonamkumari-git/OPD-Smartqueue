"""Admin-only aggregate analytics; raw personal patient records are never returned."""
from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import require_roles
from app.schemas.common import APIResponse, Role
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
service = AnalyticsService()


def ids(department_id: str | None, doctor_id: str | None) -> tuple[ObjectId | None, ObjectId | None]:
    return (ObjectId(department_id) if department_id and ObjectId.is_valid(department_id) else None, ObjectId(doctor_id) if doctor_id and ObjectId.is_valid(doctor_id) else None)


@router.get("/overview", response_model=APIResponse[dict])
async def overview(date: str | None = Query(default=None), department_id: str | None = None, doctor_id: str | None = None, _: dict = Depends(require_roles(Role.ADMIN))):
    department, doctor = ids(department_id, doctor_id)
    return APIResponse(data=await service.overview(date or service_date(), department, doctor))


@router.get("/departments", response_model=APIResponse[list[dict]])
async def departments(date: str | None = Query(default=None), doctor_id: str | None = None, _: dict = Depends(require_roles(Role.ADMIN))):
    _, doctor = ids(None, doctor_id)
    return APIResponse(data=await service.department_load(date or service_date(), doctor))


@router.get("/doctors", response_model=APIResponse[list[dict]])
async def doctors(date: str | None = Query(default=None), department_id: str | None = None, _: dict = Depends(require_roles(Role.ADMIN))):
    department, _ = ids(department_id, None)
    return APIResponse(data=await service.doctor_workload(date or service_date(), department))


@router.get("/hourly", response_model=APIResponse[list[dict]])
async def trends(date: str | None = Query(default=None), department_id: str | None = None, doctor_id: str | None = None, _: dict = Depends(require_roles(Role.ADMIN))):
    department, doctor = ids(department_id, doctor_id)
    return APIResponse(data=await service.trends(date or service_date(), department, doctor))


def service_date() -> str:
    from datetime import datetime
    return datetime.now().date().isoformat()
