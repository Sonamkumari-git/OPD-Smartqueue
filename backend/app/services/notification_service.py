"""Persisted, idempotent patient notifications with matching live delivery."""
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.repositories.core import NotificationRepository
from app.websocket.manager import manager


class NotificationService:
    def __init__(self) -> None:
        self.repository = NotificationRepository()

    async def notify_patient(self, user_id: ObjectId | None, token_id: ObjectId, patient_id: ObjectId, notification_type: str, message: str) -> None:
        if user_id is None:
            return
        dedupe_key = f"{user_id}:{token_id}:{notification_type}"
        try:
            document = {"user_id": user_id, "token_id": token_id, "type": notification_type, "message": message, "is_read": False, "dedupe_key": dedupe_key, "created_at": datetime.now().astimezone()}
            await self.repository.create(document)
        except DuplicateKeyError:
            return
        await manager.broadcast_to_patient(str(patient_id), {"event": notification_type, "token_id": str(token_id), "message": message})

    async def mark_read(self, user_id: ObjectId, notification_id: ObjectId) -> dict | None:
        return await self.repository.mark_read(notification_id, user_id)

    async def mark_all_read(self, user_id: ObjectId) -> int:
        return await self.repository.mark_all_read(user_id)

    async def audit(self, user_id: ObjectId | None, action: str, entity_type: str, entity_id: ObjectId, metadata: dict | None = None) -> None:
        await self.repository.create_audit_log({"user_id": user_id, "action": action, "entity_type": entity_type, "entity_id": entity_id, "metadata": metadata or {}, "timestamp": datetime.now().astimezone()})
