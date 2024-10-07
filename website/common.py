import os, json
import time


def unixtime():
    return time.time()


def get_config():
    with open(os.environ["HYBRIDOCR_CONFIG_FILE"], "r") as fd:
        config = json.loads(fd.read())
    config["production"] = config["flask"].get("production", False)
    return config


async def open_database(config):
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(
        host=config["mongodb"]["uri"],
        username=config["mongodb"]["username"],
        password=config["mongodb"]["password"],
    )

    db = client[config["mongodb"]["dbname"]]
    col_log = db.get_collection("log")
    await col_log.insert_one({"boot": unixtime()})
    return client, db


async def open_redis(config):
    import redis.asyncio as aioredis
    node = config["redis"]["node"][0]
    client = aioredis.Redis(
        host=node["host"],
        port=node["port"],
        password=config["redis"]["auth"]["password"],
        encoding="utf-8",
    )
    await client.set("test", "test")
    await client.delete("test")
    return client
