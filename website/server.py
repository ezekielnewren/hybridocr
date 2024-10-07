## python3 -m fastapi dev server.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import json
from pathlib import Path

from starlette.middleware import Middleware

from website import common
from website.session import SessionMiddleware

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
    Middleware(SessionMiddleware)
]

app = FastAPI(lifespan=lifespan, middleware=middleware)


@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse('index.html', {
        "request": request,
        "production": app.state.config["production"],
        "gtag_id": app.state.config["flask"]["gtag_id"],
    })


@app.get('/register')
async def register(request: Request):
    return templates.TemplateResponse('register.html', {
        "request": request,
        "production": app.state.config["production"],
        "gtag_id": app.state.config["flask"]["gtag_id"],
    })


@app.get('/about')
async def about(request: Request):
    return templates.TemplateResponse('about.html', {
        "request": request,
        "production": app.state.config["production"],
        "gtag_id": app.state.config["flask"]["gtag_id"],
    })


@app.post('/save-email')
async def save_email(request: Request):
    body = json.loads(await request.body())
    body["timestamp"] = common.unixtime()
    col_analytics = app.state.db.get_collection("analytics")
    col_analytics.insert_one(body)
    return json.dumps({"result": "ok"})
