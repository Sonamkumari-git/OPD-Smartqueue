"""Public department and doctor availability endpoints."""
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from app.repositories.core import CatalogRepository
from app.schemas.common import APIResponse
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api", tags=["catalog"])
catalog = CatalogRepository()


@router.get("/departments", response_model=APIResponse[list[dict]])
async def list_departments():
    return APIResponse(data=[serialize_document(item) for item in await catalog.list_departments()])


@router.get("/departments/{department_id}", response_model=APIResponse[dict])
async def get_department(department_id: str):
    if not ObjectId.is_valid(department_id):
        raise HTTPException(status_code=422, detail="Invalid department identifier.")
    department = await catalog.get_department(ObjectId(department_id))
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found.")
    return APIResponse(data=serialize_document(department))


@router.get("/doctors", response_model=APIResponse[list[dict]])
async def list_doctors(department_id: str | None = Query(default=None)):
    department_object_id = ObjectId(department_id) if department_id and ObjectId.is_valid(department_id) else None
    doctors = await catalog.list_doctors(department_object_id)
    user_map = await catalog.get_users_by_ids([doctor["user_id"] for doctor in doctors])
    result = []
    for doctor in doctors:
        item = serialize_document(doctor)
        item["name"] = user_map.get(doctor["user_id"], {}).get("name", "Assigned clinician")
        result.append(item)
    return APIResponse(data=result)


@router.get("/doctors/{doctor_id}/availability", response_model=APIResponse[dict])
async def doctor_availability(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(status_code=422, detail="Invalid doctor identifier.")
    doctor = await catalog.get_doctor(ObjectId(doctor_id))
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return APIResponse(data={"doctor_id": doctor_id, "status": doctor["status"], "available": doctor["status"] == "AVAILABLE"})
