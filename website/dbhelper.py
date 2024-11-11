from motor.motor_asyncio import AsyncIOMotorDatabase


async def init(db: AsyncIOMotorDatabase, t):
    col_log = db.get_collection("log")
    await col_log.insert_one({"boot": t})

    col_user = db.get_collection("user")
    await col_user.create_index("username", unique=True)







