# from flask import Flask, request, render_template

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import json

from website import common

config = common.get_config()
client, db = common.open_database(config)
rd = common.open_redis(config)
templates = Jinja2Templates(directory="templates")


app = FastAPI()


@app.get('/')
# async def root():
#     return "hello world"

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

