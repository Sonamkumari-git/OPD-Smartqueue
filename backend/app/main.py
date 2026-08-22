"""FastAPI entry point for the local OPD SmartQueue backend."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database.indexes import create_indexes
from app.database.mongodb import close_mongo_connection, connect_to_mongo, is_mongo_ready
from app.routers import analytics, auth, catalog, doctor, notifications, nurse, patient, predictions, queue, vitals, websocket
from app.utils.errors import AppError, ServiceUnavailableError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("opd_smartqueue")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_production and not settings.has_safe_jwt_secret:
        raise RuntimeError("JWT_SECRET must be set to a non-default value of at least 32 characters in production.")
    try:
        await connect_to_mongo()
        await create_indexes()
        logger.info("MongoDB connected and indexes verified.")
    except Exception as exc:
        logger.error("MongoDB startup check failed: %s", exc)
    yield
    await close_mongo_connection()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.message, "error_code": exc.error_code})


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request could not be completed."
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": message, "error_code": f"HTTP_{exc.status_code}"})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"success": False, "message": "Request validation failed.", "error_code": "VALIDATION_ERROR", "details": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled API error: %s", exc)
    return JSONResponse(status_code=500, content={"success": False, "message": "An unexpected server error occurred.", "error_code": "INTERNAL_ERROR"})


@app.get("/health")
async def health():
    return {"success": True, "data": {"service": settings.app_name, "environment": settings.app_env, "database_ready": await is_mongo_ready()}, "message": "API process is running."}


@app.get("/ready")
async def ready():
    if not await is_mongo_ready():
        raise ServiceUnavailableError("MongoDB is unavailable; the API is not ready to serve operational requests.")
    return {"success": True, "data": {"ready": True}, "message": "API and MongoDB are ready."}


app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(patient.router)
app.include_router(queue.router)
app.include_router(doctor.router)
app.include_router(vitals.router)
app.include_router(nurse.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(websocket.router)
