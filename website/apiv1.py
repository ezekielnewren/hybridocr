import json
from pathlib import Path

import aiohttp
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
    not_authorized = Response(util.compact_json({"errors": ["unauthorized"]}), status_code=400, media_type="application/json")



    cf_turnstile_response = request.headers.get("cf-turnstile-response")
    secret_key = (await ctx.vault.kv_get(Path("kv/api_token/cloudflare_turnstile")))["secret"]

    data = {
        "secret": secret_key,
        "response": cf_turnstile_response,
    }
    async with aiohttp.request("POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data) as r:
        content = await r.content.read()
    content = json.loads(content)

    if not content.get("success"):
        return not_authorized

    auth = request.headers.get("Authorization")
    p = re.compile("^([^:]+):([^:]+)$")

    m = p.match(auth)
    if not bool(m):
        return not_authorized

    _id = m.group(1)
    challenge = m.group(2)

    r = await rdhelper.get_str(ctx.rm.redis, str(Path(f"/user/{_id}/challenge")))
    if r != challenge:
        return not_authorized

    image = await request.body()

    run_ocr = lambda _image: ctx.gocr.ocr(_image)

    _id = ObjectId(_id)
    ticket = await ctx.credit.debit_p1(_id)
    if ticket["state"] == dbhelper.EMPTY:
        return Response(util.compact_json({"errors": ["no more scans left"]}), status_code=400, media_type="application/json")
    elif ticket["state"] == dbhelper.CONTENTION:
        return Response(util.compact_json({"errors": ["try again later"]}), status_code=400, media_type="application/json")
    try:
        if not ctx.config["production"]:
            name = Path(util.compute_hash(image).hex())
            v = await rdhelper.file_get(ctx.rm.redis, name)
            if v is None:
                answer = await run_ocr(image)
                await rdhelper.file_put(ctx.rm.redis, name, answer, expire=30*86400)

            v = await rdhelper.file_get(ctx.rm.redis, name)
            if v is None:
                raise ValueError("file must have been deleted or expired")
            _, answer = v
        else:
            answer = await run_ocr(image)

        await ctx.credit.debit_p2(_id, ticket["challenge"], True)
        return Response(answer, media_type="application/json")
    except Exception as e:
        await ctx.credit.debit_p2(_id, ticket["challenge"], False)
        return Response(util.compact_json({"errors": ["error when running ocr"]}), status_code=500, media_type="application/json")


