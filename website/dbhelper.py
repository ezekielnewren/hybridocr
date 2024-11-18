from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from website import common, rdhelper

PROCEED = 0
CONTENTION = 1
EMPTY = 2

async def init(db: AsyncIOMotorDatabase, t):
    col_log = db.get_collection("log")
    await col_log.insert_one({"boot": t})

    col_user = db.get_collection("user")
    await col_user.create_index("username", unique=True)

async def ensure_user_exists(db: AsyncIOMotorDatabase, t: float, username: str, plan: str = "trial"):
    user_data = {
        "username": username,
        "created": t,
        "plan": plan,
        "scan": {
            "google": {
                "count": 0,
                "limit": 10,
                "pending": []
            }
        }
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


async def inc_scan_p1(db: AsyncIOMotorDatabase, _id: ObjectId, time: float, challenge=None):
    await db.user.update_one(
        {"_id": _id},
        {
            "$pull": {
                "scan.google.pending": {
                    "expire": {"$lt": time}
                }
            }
        }
    )

    if challenge is None:
        challenge = common.generate_alphanumeric(32)
    ticket = {
        "challenge": challenge,
        "expire": time + 300
    }

    result = await db.user.find_one_and_update(
        {"_id": _id},
        [
            {
                "$set": {
                    "scan.google.pending": {
                        "$cond": {
                            "if": {
                                "$lt": [
                                    {"$add": ["$scan.google.count", {"$size": "$scan.google.pending"}]},
                                    "$scan.google.limit"
                                ]
                            },
                            "then": {"$concatArrays": ["$scan.google.pending", [ticket]]},
                            "else": "$scan.google.pending"
                        }
                    }
                }
            }
        ],
        return_document=ReturnDocument.BEFORE)

    a = result["scan"]["google"]["count"]
    b = len(result["scan"]["google"]["pending"])
    c = result["scan"]["google"]["limit"]

    if a >= c:
        return {"state": EMPTY}
    elif a + b >= c and result["scan"]["google"]["pending"]:
        return {"state": CONTENTION}
    else:
        assert a + b < c
        ticket["state"] = PROCEED
        return ticket


async def inc_scan_p2(db: AsyncIOMotorDatabase, _id: ObjectId, challenge, commit):
    if commit:
        await db.user.find_one_and_update(
            {"_id": _id},
            {
                "$inc": {"scan.google.count": 1},
                "$pull": {"scan.google.pending": {"challenge": challenge}}
            }
        )
    else:
        await db.user.find_one_and_update(
            {"_id": _id},
            {
                "$pull": {"scan.google.pending": {"challenge": challenge}}
            }
        )


async def user_exists(db, _id):
    return await db.user.find_one({"_id": _id}) is not None
