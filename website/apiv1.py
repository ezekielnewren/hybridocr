import rdhelper
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
        for name, v in batch.items():
            put = True
            if await rdhelper.file_exists(ctx.redis, name):
                meta, data = await rdhelper.file_get(ctx.redis, name)
                put = meta["hash"] != common.compute_hash(v)

            if put:
                await rdhelper.file_put(ctx.redis, name, v)
            else:
                await rdhelper.file_touch(ctx.redis, name)

    return {"received": [str(v) for v in batch.keys()]}
