## python3 -m uvicorn website.server:app --reload --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'
from contextlib import asynccontextmanager

from bson import ObjectId
from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates

import json
from pathlib import Path

from starlette.staticfiles import StaticFiles

from website.apiv1 import router as apiv1_router
from starlette.middleware import Middleware

from website import util, rdhelper, dbhelper
from website.middleware import SessionMiddleware, get_context, StaticMiddleware
import os
from email_validator import validate_email, EmailNotValidError

templates = Jinja2Templates(directory=Path(__file__).parent/"templates")
dir_static = Path(__file__).parent/"static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = get_context(app)
    await ctx.init()
    yield
    ctx.rm.client.close()


middleware = [
    Middleware(SessionMiddleware),
    Middleware(StaticMiddleware),
]

app = FastAPI(lifespan=lifespan, middleware=middleware)
app.include_router(apiv1_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=dir_static), name="static")

@app.get('/')
async def home(request: Request):
    ctx = get_context(app)
    return templates.TemplateResponse('index.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
    })


@app.get("/tryitout")
async def tryitout(request: Request):
    ctx = get_context(app)
    _id = util.str2ObjectId(request.query_params.get("_id"))
    doc = await ctx.rm.db.user.find_one({"_id": _id})
    need_email = doc is None
    if doc is not None and not doc["email_verified"]:
        await ctx.rm.db.user.find_one_and_update(
            {"_id": _id},
            {"$set": {"email_verified": True}})
    challenge = request.query_params.get("challenge")
    if challenge is None:
        need_challenge = True
    else:
        r = await rdhelper.get_str(ctx.rm.redis, f"/user/{util.ObjectId2str(_id)}/challenge")
        need_challenge = r is None or r != challenge
    need_challenge = need_challenge or need_email
    if need_email or need_challenge:
        return templates.TemplateResponse('tryitout.html', {
            "request": request,
            "production": ctx.config["production"],
            "gtag_id": ctx.config["webserver"]["gtag_id"],
            "need_email": need_email,
            "need_challenge": need_challenge,
        })
    doc = await ctx.rm.db.user.find_one({"_id": _id})
    cf_secret = await ctx.vault.kv_get(Path("kv/api_token/cloudflare_turnstile"))
    balance = await ctx.credit.balance(_id)
    return templates.TemplateResponse('tryitout.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
        "username": doc["username"],
        "balance": balance,
        "cf_site": cf_secret["site"],
    })


@app.get("/status/ip")
async def ip(request: Request):
    return Response(request.client.host, media_type="text/plain")


@app.get("/status/alive")
async def alive(request: Request):
    return Response("Alive!", media_type="text/plain")


@app.get("/status/ready")
async def ready(request: Request):
    return Response("Ready!", media_type="text/plain")


@app.get("/info")
async def info(request: Request):
    ctx = get_context(app)
    if ctx.config["production"]:
        return Response("", media_type="text/plain")
    name = os.environ.get("POD_NAME")
    namespace = os.environ.get("POD_NAMESPACE")
    return Response(f"name: {name}\nnamespace: {namespace}", media_type="text/plain")


@app.get('/check-your-email')
async def check_your_email(request: Request):
    ctx = get_context(app)
    return templates.TemplateResponse('check-your-email.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
    })


@app.get('/about')
async def about(request: Request):
    ctx = get_context(app)
    return templates.TemplateResponse('about.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
    })


@app.post('/register')
async def register(request: Request):
    ctx = get_context(app)
    body = json.loads(await request.body())
    body["timestamp"] = await ctx.rm.get_time()

    if "_id" in body:
        body["_id"] = util.str2ObjectId(body["_id"])
        result = await ctx.rm.db.user.find_one({"_id": body["_id"]})
        body["email"] = result["username"]
    elif "email" in body:
        result = await dbhelper.ensure_user_exists(ctx.rm.db, body["timestamp"], body["email"])
        body["_id"] = util.str2ObjectId(result["_id"])
    else:
        return Response(util.compact_json({"errors": ["must supply email or _id"]}), status_code=400, media_type="text/application")
    assert "_id" in body and "email" in body
    try:
        body["email"] = validate_email(body["email"], check_deliverability=ctx.config["production"])
    except EmailNotValidError as e:
        return Response(util.compact_json({"errors": [str(e)]}), status_code=400, media_type="application/json")
    prohibited_email_domain = ctx.config["webserver"].get("prohibited_email_domain")
    if prohibited_email_domain is not None and body["email"].domain in prohibited_email_domain:
        return Response(util.compact_json({"errors": ["Prohibited email address"]}), status_code=400, media_type="application/json")

    key = str(Path(f"/user/{util.ObjectId2str(body['_id'])}/challenge"))
    challenge = await rdhelper.get_str(ctx.rm.redis, key)
    if challenge is None:
        challenge = util.generate_alphanumeric(32)
        await ctx.rm.redis.set(key, challenge, ex=5*3600)


    link = "https://"+ctx.config["webserver"]["domain"][0]+f"/tryitout?_id={util.ObjectId2str(body['_id'])}&challenge={challenge}"
    email_body = "here is your link for 10 free scans "+link
    await ctx.gmail.send_email("noreply", body["email"], "10 free scans link", email_body)
    return Response(util.compact_json({"success": True}), status_code=200, media_type="application/json")
