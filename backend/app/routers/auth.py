"""Authentication endpoints."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["authentication"])
service = AuthService()


@router.post("/register", response_model=APIResponse[dict], status_code=201)
async def register(payload: RegisterRequest):
    return APIResponse(data=await service.register_patient(payload), message="Patient account created.")


@router.post("/login", response_model=APIResponse[dict])
async def login(payload: LoginRequest):
    return APIResponse(data=await service.login(payload), message="Login successful.")


@router.get("/me", response_model=APIResponse[dict])
async def me(current_user: dict = Depends(get_current_user)):
    return APIResponse(data=service.public_user(current_user))
