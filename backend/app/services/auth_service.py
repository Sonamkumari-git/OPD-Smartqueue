"""Registration and JWT login service for patient self-service accounts."""
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import get_settings
from app.repositories.core import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.errors import AppError, ConflictError
from app.utils.serializers import serialize_document
from app.database.mongodb import get_database


class AuthService:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.settings = get_settings()

    @staticmethod
    def public_user(document: dict) -> dict:
        result = serialize_document(document) or {}
        result.pop("password_hash", None)
        return result

    async def register_patient(self, payload: RegisterRequest) -> dict:
        email = payload.email.lower()
        if await self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists.")
        now = datetime.now().astimezone()
        user_document = {
            "name": payload.name.strip(),
            "email": email,
            "phone": payload.phone,
            "password_hash": hash_password(payload.password),
            "role": "patient",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        try:
            user = await self.users.create(user_document)
        except DuplicateKeyError as exc:
            raise ConflictError("An account with this email already exists.") from exc
        await get_database().patients.insert_one({
            "user_id": user["_id"],
            "date_of_birth": payload.date_of_birth.isoformat() if payload.date_of_birth else None,
            "gender": payload.gender,
            "emergency_contact": payload.emergency_contact,
            "created_at": now,
            "updated_at": now,
        })
        return self.issue_token(user)

    async def login(self, payload: LoginRequest) -> dict:
        user = await self.users.get_by_email(payload.email.lower())
        if user is None or not user.get("is_active") or not verify_password(payload.password, user["password_hash"]):
            raise AppError("Invalid email or password.", "INVALID_CREDENTIALS", 401)
        return self.issue_token(user)

    def issue_token(self, user: dict) -> dict:
        return {
            "access_token": create_access_token(str(user["_id"]), user["role"]),
            "token_type": "bearer",
            "expires_in_minutes": self.settings.access_token_expire_minutes,
            "user": self.public_user(user),
        }
