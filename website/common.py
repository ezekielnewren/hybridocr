import os, json
import time
import cbor2


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


def open_redis(config):
    import redis.asyncio as aioredis
    node = config["redis"]["node"][0]
    return aioredis.Redis(
        host=node["host"],
        port=node["port"],
        password=config["redis"]["auth"]["password"],
        encoding="utf-8",
    )


def to_cbor(data):
    return cbor2.dumps(data)


def from_cbor(data):
    return cbor2.loads(data)
