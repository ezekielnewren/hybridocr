from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

PROCEED = 0
CONTENTION = 1
EMPTY = 2
BUSY = 3

async def init(db: AsyncIOMotorDatabase, t):
    col_log = db.get_collection("log")
    await col_log.insert_one({"boot": t})

    col_user = db.get_collection("user")
    await col_user.create_index("username", unique=True)

async def ensure_user_exists(db: AsyncIOMotorDatabase, t: float, username: str, plan: str = "trial"):
    user_data = {
        "created": t,
        "plan": plan,
        "marketing": False,
        "email_verified": False,
        "username": username,
    }

    result = await db.user.find_one_and_update(
        {"username": username},
        {"$setOnInsert": user_data},
        upsert=True,
        return_document=True
    )

    return result


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str):
    return await db.user.find_one({"username": username})


async def get_user_by_id(db: AsyncIOMotorDatabase, _id: ObjectId):
    return await db.user.find_one({"_id": _id})


async def user_exists(db, _id):
    return await db.user.find_one({"_id": _id}) is not None
