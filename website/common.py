from google.cloud.vision_v1 import AnnotateImageResponse
from redis.asyncio import Redis
import os, json
import hashlib
import time
import cbor2
from pathlib import Path

from website.hcvault import VaultClient


DOMAIN = "hybridocr.com"


def unixtime():
    return time.time()


async def get_config():
    with open(os.environ["HYBRIDOCR_CONFIG_FILE"], "r") as fd:
        config = json.loads(fd.read())
    vault = VaultClient(config["vault"]["VAULT_ADDR"], config["vault"]["VAULT_TOKEN"])

    result = await vault.read(Path("auth/token/lookup-self"))
    env = result["data"]["meta"]["env"]
    config = await vault.kv_get(Path("kv/env/"+env))
    config["production"] = config["webserver"].get("production") or False
    return config


def open_database(config):
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(
        host=config["mongodb"]["uri"],
        username=config["mongodb"]["username"],
        password=config["mongodb"]["password"],
    )

    db = client[config["mongodb"]["dbname"]]
    return client, db


def open_redis(config):
    node = config["redis"]["node"][0]
    return Redis(
        host=node["host"],
        port=node["port"],
        username=config["redis"]["auth"].get("username"),
        password=config["redis"]["auth"].get("password"),
        encoding="utf-8",
        db=config["redis"]["db"],
    )


from google.cloud import vision
from google.auth import default

def google_ocr(image) -> bytes:
    cred, proj = default()
    client = vision.ImageAnnotatorClient(credentials=cred)
    img = vision.Image(content=image)
    answer = client.text_detection(image=img)
    return compact_json(AnnotateImageResponse.to_json(answer)).encode("utf-8")

def to_cbor(data):
    return cbor2.dumps(data)


def from_cbor(data):
    return cbor2.loads(data)


def compute_hash(data):
    return hashlib.sha256(data).digest()


def compact_json(data):
    if isinstance(data, str) or isinstance(data, bytes):
        data = json.loads(data)
    return json.dumps(data, separators=(',', ':'))


def check_type(obj, t_type):
    if not isinstance(obj, t_type):
        raise TypeError("expected type: "+str(t_type)+" but got "+str(type(obj)))


def exists(data, path):
    if data is None:
        return False
    if not isinstance(data, dict):
        raise TypeError("data must be a dict")
    if not isinstance(path, list):
        raise TypeError("path must be a list")
    cur = data
    for i in range(len(path)):
        if path[i] not in cur:
            return False
        cur = cur[path[i]]
    return True
