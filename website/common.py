from redis.asyncio import Redis
from pathlib import Path
import os, json
import hashlib
import time
import cbor2


def unixtime():
    return time.time()


def get_config():
    with open(os.environ["HYBRIDOCR_CONFIG_FILE"], "r") as fd:
        config = json.loads(fd.read())
    config["production"] = config["webserver"].get("production", False)
    return config


def open_database(config):
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(
        host=config["mongodb"]["uri"],
        username=config["mongodb"]["username"],
        password=config["mongodb"]["password"],
    )

    db = client[config["mongodb"]["dbname"]]
    return client, db


def open_redis(config):
    node = config["redis"]["node"][0]
    return Redis(
        host=node["host"],
        port=node["port"],
        password=config["redis"]["auth"]["password"],
        encoding="utf-8",
        db=config["redis"]["db"],
    )


def to_cbor(data):
    return cbor2.dumps(data)


def from_cbor(data):
    return cbor2.loads(data)


async def get_time(rd):
    sec, micro = await rd.time()
    return sec + float(micro)/1000000.0


def compute_hash(data):
    b = hashlib.sha256()
    b.update(data)
    return b.digest()


async def redis_file_exists(rd: Redis, path):
    prefix = Path("/file")
    full_path = str((prefix / path).absolute())
    return await rd.exists(full_path)


async def redis_put_file(rd: Redis, path, data, expire=None):
    prefix = Path("/file")
    full_path = str((prefix/path).absolute())

    meta = dict()
    meta["size"] = len(data)
    meta["access"] = await get_time(rd)
    if expire:
        meta["expire"] = expire
    meta["hash"] = compute_hash(data)

    payload = to_cbor(meta)

    await rd.hset(full_path, mapping={"meta": payload, "data": data})

    if expire:
        await rd.expire(full_path, expire)

    await rd.zadd("/file", mapping={full_path: meta["access"]})


async def redis_get_file(rd: Redis, path):
    prefix = Path("/file")
    full_path = str((prefix/path).absolute())

    if not await rd.exists(full_path):
        return None

    meta = from_cbor(await rd.hget(full_path, "meta"))
    data = from_cbor(await rd.hget(full_path, "data"))
    await redis_touch_file(rd, path)

    return meta, data


async def redis_touch_file(rd: Redis, path):
    prefix = Path("/file")
    full_path = str((prefix/path).absolute())

    if not await rd.exists(full_path):
        return None

    meta = from_cbor(await rd.hget(full_path, "meta"))
    meta["access"] = await get_time(rd)
    await rd.hset(full_path, "meta", to_cbor(meta))
    await rd.zadd("/file", mapping={full_path: meta["access"]})

    expire = meta.get("expire")
    if expire:
        await rd.expire(full_path, expire)
