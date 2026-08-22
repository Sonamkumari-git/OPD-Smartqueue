"""Create indexes, core departments, and an optional local demonstration administrator."""
import argparse
import asyncio
from datetime import datetime
from app.auth.security import hash_password
from app.database.indexes import create_indexes
from app.database.mongodb import close_mongo_connection, connect_to_mongo, get_database

DEFAULT_DEPARTMENTS = [
    {"name": "Cardiology", "code": "C", "description": "Cardiology OPD"},
    {"name": "General Medicine", "code": "M", "description": "General Medicine OPD"},
    {"name": "ENT", "code": "E", "description": "Ear, nose, and throat OPD"},
]


async def ensure_departments() -> None:
    db = get_database()
    now = datetime.now().astimezone()
    for department in DEFAULT_DEPARTMENTS:
        await db.departments.update_one({"code": department["code"]}, {"$set": {**department, "is_active": True, "updated_at": now}, "$setOnInsert": {"created_at": now}}, upsert=True)


async def initialize(with_demo_admin: bool = False) -> None:
    await connect_to_mongo()
    try:
        await create_indexes()
        await ensure_departments()
        if with_demo_admin:
            db = get_database()
            now = datetime.now().astimezone()
            await db.users.update_one({"email": "admin@opdsmartqueue.local"}, {"$setOnInsert": {"name": "Demo Administrator", "email": "admin@opdsmartqueue.local", "phone": None, "password_hash": hash_password("DemoPass!123"), "role": "admin", "is_active": True, "created_at": now, "updated_at": now}}, upsert=True)
        print("MongoDB connectivity verified. Indexes and departments are ready.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize OPD SmartQueue MongoDB collections and indexes.")
    parser.add_argument("--with-demo-admin", action="store_true", help="Create the local-only demo admin account.")
    args = parser.parse_args()
    asyncio.run(initialize(args.with_demo_admin))
