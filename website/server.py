## python3 -m uvicorn website.server:app --reload --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates

import json
from pathlib import Path

from apiv1 import router as apiv1_router
from starlette.middleware import Middleware

from website import common
from website.session import SessionMiddleware, get_session
import rdhelper
import sys
import os


templates = Jinja2Templates(directory=Path(__file__).parent/"templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = get_session(app)
    col_log = ctx.db.get_collection("log")
    t = await rdhelper.get_time(ctx.redis)
    await col_log.insert_one({"boot": t})
    yield
    ctx.client.close()


middleware = [
    Middleware(SessionMiddleware),
]

app = FastAPI(lifespan=lifespan, middleware=middleware)
app.include_router(apiv1_router, prefix="/api/v1")


@app.get('/')
async def home(request: Request):
    ctx = get_session(app)
    return templates.TemplateResponse('index.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
    })


@app.get("/upload")
async def upload(request: Request):
    ctx = get_session(app)
    return templates.TemplateResponse('upload.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
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
    ctx = get_session(app)
    if ctx.config["production"]:
        return Response("", media_type="text/plain")
    name = os.environ.get("POD_NAME")
    namespace = os.environ.get("POD_NAMESPACE")
    return Response(f"name: {name}\nnamespace: {namespace}", media_type="text/plain")


@app.get('/register')
async def register(request: Request):
    ctx = get_session(app)
    return templates.TemplateResponse('register.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
    })


@app.get('/about')
async def about(request: Request):
    ctx = get_session(app)
    return templates.TemplateResponse('about.html', {
        "request": request,
        "production": ctx.config["production"],
        "gtag_id": ctx.config["webserver"]["gtag_id"],
    })


@app.post('/save-email')
async def save_email(request: Request):
    ctx = get_session(app)
    body = json.loads(await request.body())
    body["timestamp"] = common.unixtime()
    col_analytics = ctx.db.get_collection("analytics")
    await col_analytics.insert_one(body)
    return json.dumps({"result": "ok"})
