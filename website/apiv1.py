import rdhelper
from typing import List
from pathlib import Path

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
        batch[Path(f.filename)] = await f.read()

    if not ctx.config["production"]:
        for name, content in batch.items():
            meta = await rdhelper.file_get_meta(ctx.redis, name)
            if meta is not None and meta["hash"] != common.compute_hash(content):
                await rdhelper.file_put(ctx.redis, name, content)

    return {"received": [str(v) for v in batch.keys()]}
