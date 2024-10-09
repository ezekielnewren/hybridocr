## python3 -m uvicorn website.server:app --reload --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates

import json
from pathlib import Path

from starlette.middleware import Middleware

from website import common
from website.session import SessionMiddleware
import os

templates = Jinja2Templates(directory=Path(__file__).parent/"templates")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    app.state.config = common.get_config()
    v = await common.open_database(app.state.config)
    app.state.client = v[0]
    app.state.db = v[1]
    yield
    app.state.client.close()


middleware = [
    Middleware(SessionMiddleware),
]

app = FastAPI(lifespan=lifespan, middleware=middleware)


@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse('index.html', {
        "request": request,
        "production": app.state.config["production"],
        "gtag_id": app.state.config["webserver"]["gtag_id"],
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
    if app.state.config["production"]:
        return Response("", media_type="text/plain")
    name = os.environ.get("POD_NAME")
    namespace = os.environ.get("POD_NAMESPACE")
    return Response(f"name: {name}\nnamespace: {namespace}", media_type="text/plain")


@app.get('/register')
async def register(request: Request):
    return templates.TemplateResponse('register.html', {
        "request": request,
        "production": app.state.config["production"],
        "gtag_id": app.state.config["webserver"]["gtag_id"],
    })


@app.get('/about')
async def about(request: Request):
    return templates.TemplateResponse('about.html', {
        "request": request,
        "production": app.state.config["production"],
        "gtag_id": app.state.config["webserver"]["gtag_id"],
    })


@app.post('/save-email')
async def save_email(request: Request):
    body = json.loads(await request.body())
    body["timestamp"] = common.unixtime()
    col_analytics = app.state.db.get_collection("analytics")
    col_analytics.insert_one(body)
    return json.dumps({"result": "ok"})
