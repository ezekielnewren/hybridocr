## python3 -m fastapi dev server.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import json
from pathlib import Path

from website import common

config = common.get_config()
client, db, rd = None, None, None


templates = Jinja2Templates(directory=Path(__file__).parent/"templates")
app = FastAPI()


@app.on_event("startup")
async def lifespan():
    global config, client, db, rd
    config = common.get_config()
    client, db = await common.open_database(config)
    rd = await common.open_redis(config)
    print("done with startup")


@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse('index.html', {
        "request": request,
        "production": config["production"],
        "gtag_id": config["flask"]["gtag_id"],
    })


@app.get('/register')
async def register(request: Request):
    return templates.TemplateResponse('register.html', {
        "request": request,
        "production": config["production"],
        "gtag_id": config["flask"]["gtag_id"],
    })


@app.get('/about')
async def about(request: Request):
    return templates.TemplateResponse('about.html', {
        "request": request,
        "production": config["production"],
        "gtag_id": config["flask"]["gtag_id"],
    })


@app.post('/save-email')
async def save_email(request: Request):
    body = json.loads(await request.body())
    body["timestamp"] = common.unixtime()
    col_analytics = db.get_collection("analytics")
    col_analytics.insert_one(body)
    return json.dumps({"result": "ok"})

