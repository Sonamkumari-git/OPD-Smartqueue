"""Authorized FastAPI WebSocket endpoints with minimum-necessary channel payloads."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.auth.security import decode_access_token
from app.repositories.core import CatalogRepository, UserRepository
from app.utils.serializers import as_object_id
from app.websocket.manager import manager

router = APIRouter(tags=["realtime"])


async def websocket_user(websocket: WebSocket) -> dict | None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return None
    try:
        payload = decode_access_token(token)
        user = await UserRepository().get_by_id(as_object_id(payload["sub"], "user id"))
        if user is None or not user.get("is_active"):
            raise ValueError("Inactive user")
        return user
    except Exception:
        await websocket.close(code=1008)
        return None


@router.websocket("/ws/queue/{department_id}")
async def queue_socket(websocket: WebSocket, department_id: str):
    user = await websocket_user(websocket)
    if user is None:
        return
    channel = f"department:{department_id}"
    await manager.connect(channel, websocket)
    try:
        await manager.send_personal_message({"event": "CONNECTED", "channel": "queue", "department_id": department_id}, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)


@router.websocket("/ws/patient/{patient_id}")
async def patient_socket(websocket: WebSocket, patient_id: str):
    user = await websocket_user(websocket)
    if user is None:
        return
    patient = await CatalogRepository().get_patient_by_user_id(user["_id"])
    if user["role"] != "patient" or patient is None or str(patient["_id"]) != patient_id:
        await websocket.close(code=1008)
        return
    channel = f"patient:{patient_id}"
    await manager.connect(channel, websocket)
    try:
        await manager.send_personal_message({"event": "CONNECTED", "channel": "patient", "patient_id": patient_id}, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)


@router.websocket("/ws/doctor/{doctor_id}")
async def doctor_socket(websocket: WebSocket, doctor_id: str):
    user = await websocket_user(websocket)
    if user is None:
        return
    doctor = await CatalogRepository().get_doctor_by_user_id(user["_id"])
    if user["role"] != "doctor" or doctor is None or str(doctor["_id"]) != doctor_id:
        await websocket.close(code=1008)
        return
    channel = f"doctor:{doctor_id}"
    await manager.connect(channel, websocket)
    try:
        await manager.send_personal_message({"event": "CONNECTED", "channel": "doctor", "doctor_id": doctor_id}, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
