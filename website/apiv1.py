from io import BytesIO
from typing import List

from fastapi import APIRouter, UploadFile, File
from fastapi import FastAPI, Request, Response

from website.session import SessionMiddleware, get_session

import common

router = APIRouter()


@router.post("/upload/")
async def upload_image(request: Request, files: List[UploadFile] = File(...)):
    ctx = get_session(request.app)

    batch = dict()

    for f in files:
        batch[f.filename] = await f.read()

    if not ctx.config["production"]:
        for name in batch:
            v = batch[name]
            if await common.redis_file_exists(ctx.redis, name):
                meta, data = await common.redis_get_file(ctx.redis, name)
                h = common.compute_hash(v)
                if h != meta["hash"]:
                    await common.redis_put_file(ctx.redis, name, v)
            else:
                await common.redis_put_file(ctx.redis, name, v)

    return {"received": [str(v) for v in batch.keys()]}
