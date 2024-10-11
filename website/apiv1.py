from io import BytesIO
from typing import List

from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/upload/")
async def upload_image(files: List[UploadFile] = File(...)):
    batch = dict()

    for f in files:
        batch[f.filename] = BytesIO(await f.read())

    return {"received": [str(v) for v in batch.keys()]}
