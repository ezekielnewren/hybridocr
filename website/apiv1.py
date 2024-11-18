from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter
from fastapi import Request, Response

from website.session import get_context
from website import rdhelper, dbhelper
from website import common
import re

router = APIRouter()


@router.post("/ocr")
async def ocr(request: Request):
    ctx = get_context(request.app)

    auth = request.headers.get("Authorization")
    p = re.compile("^([^:]+):([^:]+)$")

    not_authorized = Response(common.compact_json({"errors": ["unauthorized"]}), status_code=400, media_type="application/json")

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

    _id = ObjectId(_id)
    ticket = await dbhelper.inc_scan_p1(ctx.db, _id, t)
    if ticket["state"] == dbhelper.EMPTY:
        return Response(common.compact_json({"errors": ["no more scans left"]}), status_code=400, media_type="application/json")
    elif ticket["state"] == dbhelper.CONTENTION:
        return Response(common.compact_json({"errors": ["try again later"]}), status_code=400, media_type="application/json")
    try:
        if not ctx.config["production"]:
            name = Path(common.compute_hash(image).hex())
            v = await rdhelper.file_get(ctx.redis, name)
            if v is None:
                answer = await ctx.gocr.ocr(image)
                await rdhelper.file_put(ctx.redis, name, answer, expire=30*86400)

            v = await rdhelper.file_get(ctx.redis, name)
            if v is None:
                raise ValueError("file must have been deleted or expired")
            _, answer = v
        else:
            answer = common.google_ocr(image)

        await dbhelper.inc_scan_p2(ctx.db, _id, ticket["challenge"], True)
        return Response(answer, media_type="application/json")
    except Exception as e:
        await dbhelper.inc_scan_p2(ctx.db, _id, ticket.get("challenge"), False)
        return Response(common.compact_json({"errors": ["error when running ocr"]}), status_code=500, media_type="application/json")


