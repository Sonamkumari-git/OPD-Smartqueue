"""FastAPI dependencies for authenticated, role-limited request handling."""
from collections.abc import Callable
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.auth.security import decode_access_token
from app.repositories.core import UserRepository
from app.schemas.common import Role
from app.utils.errors import ForbiddenError, NotFoundError
from app.utils.serializers import as_object_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        from app.utils.errors import AppError
        raise AppError("Authentication is required.", "AUTH_REQUIRED", 401)
    payload = decode_access_token(credentials.credentials)
    user = await UserRepository().get_by_id(as_object_id(payload["sub"], "user id"))
    if user is None or not user.get("is_active", False):
        raise NotFoundError("Active user account not found.")
    return user


def require_roles(*allowed_roles: Role) -> Callable:
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in {role.value for role in allowed_roles}:
            raise ForbiddenError()
        return current_user
    return dependency
