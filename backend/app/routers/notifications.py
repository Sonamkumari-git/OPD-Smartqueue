"""Patient notification read-state routes backed by MongoDB ownership checks."""
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_roles
from app.schemas.common import APIResponse, Role
from app.services.notification_service import NotificationService
from app.utils.errors import NotFoundError
from app.utils.serializers import serialize_document

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
service = NotificationService()


@router.patch("/{notification_id}/read", response_model=APIResponse[dict])
async def mark_read(notification_id: str, current_user: dict = Depends(require_roles(Role.PATIENT))):
    if not ObjectId.is_valid(notification_id):
        raise NotFoundError("Notification not found.")
    notification = await service.mark_read(current_user["_id"], ObjectId(notification_id))
    if notification is None:
        raise NotFoundError("Notification not found.")
    return APIResponse(data=serialize_document(notification), message="Notification marked as read.")


@router.patch("/read-all", response_model=APIResponse[dict])
async def mark_all_read(current_user: dict = Depends(require_roles(Role.PATIENT))):
    count = await service.mark_all_read(current_user["_id"])
    return APIResponse(data={"updated": count}, message="Notifications marked as read.")
