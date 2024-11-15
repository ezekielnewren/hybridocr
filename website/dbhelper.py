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

async def upsert_user(db: AsyncIOMotorDatabase, username: str):
    challenge = common.generate_alphanumeric(32)
    user_data = {
        "auth": {
            "challenge": challenge
        },
        "scan": {
            "google": {
                "count": 0,
                "limit": 10,
                "pending": []
            }
        }
    }

    result = await db.user.find_one_and_update(
        {"username": username},  # Query to match the user
        {"$set": user_data},  # Update the user data
        upsert=True,  # Insert a new document if it doesn't exist
        return_document=True  # Return the updated document
    )

    return result

async def get_user_by_username(db: AsyncIOMotorDatabase, username: str):
    return await db.user.find_one({"username": username})

async def get_user_by_id(db: AsyncIOMotorDatabase, _id: ObjectId):
    return await db.user.find_one({"_id": _id})

async def inc_scan_p1(db: AsyncIOMotorDatabase, _id: ObjectId, time: float):
    ticket = {
        "challenge": common.generate_alphanumeric(32),
        "expire": time + 300
    }

    result = await db.user.find_one_and_update(
        {
            "_id": _id,
            "$expr": {
                "$lt": [
                    {"$add": ["$scan.google.count", {"$size": "$scan.google.pending"}]},
                    "$scan.google.limit"
                ]
            }
        },
        {
            "$push": {"scan.google.pending": ticket}
        },
        return_document=ReturnDocument.AFTER)

    a = result["scan"]["google"]["count"]
    b = len(result["scan"]["google"]["pending"])
    c = result["scan"]["google"]["limit"]

    if a + b >= c:
        if b > 0:
            return {"state": CONTENTION}
        else:
            return {"state": EMPTY}
    else:
        ticket["state"] = PROCEED
        return ticket


async def inc_scan_p2(db: AsyncIOMotorDatabase, _id: ObjectId, time: float, challenge, commit):
    if commit:
        result = await db.user.find_one_and_update(
            {
                "_id": _id
            },
            {
                "$inc": {"scan.google.count": 1},
                "$pull": {"scan.google.pending": {"challenge": challenge}}
            },
            return_document=True
        )
    else:
        result = await db.user.find_one_and_update(
            {
                "_id": _id
            },
            {
                "$pull": {"scan.google.pending": {"challenge": challenge}}
            }
        )

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

    return result

