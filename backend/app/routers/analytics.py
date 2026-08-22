"""Admin-only aggregate analytics; raw personal patient records are never returned."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.schemas.common import APIResponse, Role
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
service = AnalyticsService()


@router.get("/overview", response_model=APIResponse[dict])
async def overview(_: dict = Depends(require_roles(Role.ADMIN))):
    return APIResponse(data=await service.overview(service_date()))


@router.get("/departments", response_model=APIResponse[list[dict]])
async def departments(_: dict = Depends(require_roles(Role.ADMIN))):
    return APIResponse(data=await service.department_load(service_date()))


@router.get("/doctors", response_model=APIResponse[list[dict]])
async def doctors(_: dict = Depends(require_roles(Role.ADMIN))):
    return APIResponse(data=await service.doctor_workload(service_date()))


@router.get("/hourly", response_model=APIResponse[list[dict]])
async def hourly(_: dict = Depends(require_roles(Role.ADMIN))):
    return APIResponse(data=await service.hourly_load(service_date()))


def service_date() -> str:
    from datetime import datetime
    return datetime.now().date().isoformat()
