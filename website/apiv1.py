from google.cloud.vision_v1 import AnnotateImageResponse

import rdhelper
from typing import List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File
from fastapi import FastAPI, Request, Response

from website.session import SessionMiddleware, get_session

import common

router = APIRouter()

from google.protobuf import json_format


@router.post("/upload/")
async def upload_image(request: Request, file: UploadFile = File(...)):
    ctx = get_session(request.app)

    c = await file.read()

    if not ctx.config["production"]:
        name = Path(common.compute_hash(c).hex())
        v = await rdhelper.file_get(ctx.redis, name)
        if v is None:
            answer = common.google_ocr(c)
            ser = AnnotateImageResponse.to_json(answer).encode("utf-8")
            await rdhelper.file_put(ctx.redis, name, ser, expire=30*86400)

        v = await rdhelper.file_get(ctx.redis, name)
        if v is None:
            raise ValueError("file must have been deleted or expired")
        meta, data = v
        answer = AnnotateImageResponse.from_json(data)
    else:
        answer = common.google_ocr(c)

    return Response(AnnotateImageResponse.to_json(answer).encode("utf-8"), media_type="application/json")
