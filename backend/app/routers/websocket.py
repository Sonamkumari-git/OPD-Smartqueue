"""Authorized FastAPI WebSocket endpoints with minimum-necessary channel payloads."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.auth.security import decode_access_token
from app.database.mongodb import get_database
from app.repositories.core import CatalogRepository, UserRepository
from app.utils.serializers import as_object_id
from app.websocket.manager import manager

router = APIRouter(tags=["realtime"])


def websocket_token(websocket: WebSocket) -> str | None:
    """Read a bearer token from the negotiated WebSocket subprotocol, never a URL query."""
    protocols = [value.strip() for value in websocket.headers.get("sec-websocket-protocol", "").split(",") if value.strip()]
    if len(protocols) >= 2 and protocols[0] == "opd-smartqueue":
        return protocols[1]
    return None


async def websocket_user(websocket: WebSocket) -> dict | None:
    token = websocket_token(websocket)
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


async def can_access_department(user: dict, department_id: str) -> bool:
    if user["role"] == "admin":
        return True
    if user["role"] == "doctor":
        doctor = await CatalogRepository().get_doctor_by_user_id(user["_id"])
        return doctor is not None and str(doctor["department_id"]) == department_id
    if user["role"] == "nurse":
        return department_id in {str(value) for value in user.get("department_ids", [])}
    if user["role"] == "patient":
        if len(department_id) != 24 or any(character not in "0123456789abcdef" for character in department_id.lower()):
            return False
        return await get_database().tokens.find_one({"patient_user_id": user["_id"], "department_id": as_object_id(department_id, "department id"), "status": {"$in": ["WAITING", "CALLED", "IN_CONSULTATION"]}}) is not None
    return False


@router.websocket("/ws/queue/{department_id}")
async def queue_socket(websocket: WebSocket, department_id: str):
    user = await websocket_user(websocket)
    if user is None or not await can_access_department(user, department_id):
        if user is not None:
            await websocket.close(code=1008)
        return
    channel = f"department:{department_id}"
    await manager.connect(channel, websocket, "opd-smartqueue")
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
    await manager.connect(channel, websocket, "opd-smartqueue")
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
    await manager.connect(channel, websocket, "opd-smartqueue")
    try:
        await manager.send_personal_message({"event": "CONNECTED", "channel": "doctor", "doctor_id": doctor_id}, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
