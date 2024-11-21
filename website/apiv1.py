from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter
from fastapi import Request, Response

from website.middleware import get_context
from website import rdhelper, dbhelper
from website import util
import re

router = APIRouter()


@router.post("/ocr")
async def ocr(request: Request):
    ctx = get_context(request.app)

    auth = request.headers.get("Authorization")
    p = re.compile("^([^:]+):([^:]+)$")

    not_authorized = Response(util.compact_json({"errors": ["unauthorized"]}), status_code=400, media_type="application/json")

    m = p.match(auth)
    if not bool(m):
        return not_authorized

    _id = m.group(1)
    challenge = m.group(2)

    r = await rdhelper.get_str(ctx.redis, str(Path(f"/user/{_id}/challenge")))
    if r != challenge:
        return not_authorized

    image = await request.body()

    t = await rdhelper.get_time(ctx.redis)

    run_ocr = lambda _image: ctx.gocr.ocr(_image)

    _id = ObjectId(_id)
    ticket = await dbhelper.inc_scan_p1(ctx.db, _id, t)
    if ticket["state"] == dbhelper.EMPTY:
        return Response(util.compact_json({"errors": ["no more scans left"]}), status_code=400, media_type="application/json")
    elif ticket["state"] == dbhelper.CONTENTION:
        return Response(util.compact_json({"errors": ["try again later"]}), status_code=400, media_type="application/json")
    try:
        if not ctx.config["production"]:
            name = Path(util.compute_hash(image).hex())
            v = await rdhelper.file_get(ctx.redis, name)
            if v is None:
                answer = await run_ocr(image)
                await rdhelper.file_put(ctx.redis, name, answer, expire=30*86400)

            v = await rdhelper.file_get(ctx.redis, name)
            if v is None:
                raise ValueError("file must have been deleted or expired")
            _, answer = v
        else:
            answer = await run_ocr(image)

        await dbhelper.inc_scan_p2(ctx.db, _id, ticket["challenge"], True)
        return Response(answer, media_type="application/json")
    except Exception as e:
        await dbhelper.inc_scan_p2(ctx.db, _id, ticket.get("challenge"), False)
        return Response(util.compact_json({"errors": ["error when running ocr"]}), status_code=500, media_type="application/json")


