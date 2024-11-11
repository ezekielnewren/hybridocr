import asyncio

import rdhelper
from pathlib import Path

from fastapi import APIRouter
from fastapi import Request, Response

from website.session import get_context

import common

router = APIRouter()


@router.post("/ocr")
async def ocr(request: Request):
    ctx = get_context(request.app)

    image = await request.body()

    if not ctx.config["production"]:
        name = Path(common.compute_hash(image).hex())
        v = await rdhelper.file_get(ctx.redis, name)
        if v is None:
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(None, common.google_ocr, image)
            await rdhelper.file_put(ctx.redis, name, answer, expire=30*86400)

        v = await rdhelper.file_get(ctx.redis, name)
        if v is None:
            raise ValueError("file must have been deleted or expired")
        _, answer = v
    else:
        answer = common.google_ocr(image)

    return Response(answer, media_type="application/json")
