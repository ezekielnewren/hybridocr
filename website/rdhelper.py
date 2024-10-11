from redis.asyncio import Redis
from pathlib import Path
import common


async def get_time(rd):
    sec, micro = await rd.time()
    return sec + float(micro)/1000000.0


async def file_exists(rd: Redis, path):
    prefix = Path("/file")
    full_path = str((prefix / path).absolute())
    return await rd.exists(full_path)


async def file_put(rd: Redis, path, data, expire=None):
    prefix = Path("/file")
    full_path = str((prefix/path).absolute())

    meta = dict()
    meta["size"] = len(data)
    meta["access"] = await get_time(rd)
    if expire:
        meta["expire"] = expire
    meta["hash"] = common.compute_hash(data)

    payload = common.to_cbor(meta)

    await rd.hset(full_path, mapping={"meta": payload, "data": data})

    if expire:
        await rd.expire(full_path, expire)

    await rd.zadd("/file", mapping={full_path: meta["access"]})


async def file_get(rd: Redis, path):
    prefix = Path("/file")
    full_path = str((prefix/path).absolute())

    if not await rd.exists(full_path):
        return None

    meta = common.from_cbor(await rd.hget(full_path, "meta"))
    data = common.from_cbor(await rd.hget(full_path, "data"))
    await file_touch(rd, path)

    return meta, data


async def file_touch(rd: Redis, path):
    prefix = Path("/file")
    full_path = str((prefix/path).absolute())

    if not await rd.exists(full_path):
        return None

    meta = common.from_cbor(await rd.hget(full_path, "meta"))
    meta["access"] = await get_time(rd)
    await rd.hset(full_path, "meta", common.to_cbor(meta))
    await rd.zadd("/file", mapping={full_path: meta["access"]})

    expire = meta.get("expire")
    if expire:
        await rd.expire(full_path, expire)
