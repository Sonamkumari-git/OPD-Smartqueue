"""Authorized WebSocket channel manager for queue, patient, and doctor events."""
import json
from collections import defaultdict
from datetime import date, datetime
from bson import ObjectId
from fastapi import WebSocket


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, ObjectId):
        return str(value)
    raise TypeError(f"Value of type {type(value).__name__} is not JSON serializable")


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._channels[channel].add(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        self._channels[channel].discard(websocket)
        if not self._channels[channel]:
            self._channels.pop(channel, None)

    async def send_personal_message(self, payload: dict, websocket: WebSocket) -> None:
        await websocket.send_text(json.dumps(payload, default=_json_default))

    async def broadcast(self, channel: str, payload: dict) -> None:
        stale: list[WebSocket] = []
        encoded = json.dumps(payload, default=_json_default)
        for websocket in self._channels.get(channel, set()).copy():
            try:
                await websocket.send_text(encoded)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(channel, websocket)

    async def broadcast_to_department(self, department_id: str, payload: dict) -> None:
        await self.broadcast(f"department:{department_id}", payload)

    async def broadcast_to_doctor(self, doctor_id: str, payload: dict) -> None:
        await self.broadcast(f"doctor:{doctor_id}", payload)

    async def broadcast_to_patient(self, patient_id: str, payload: dict) -> None:
        await self.broadcast(f"patient:{patient_id}", payload)


manager = WebSocketConnectionManager()
