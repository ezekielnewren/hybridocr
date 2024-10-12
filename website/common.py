from google.cloud.vision_v1 import AnnotateImageResponse
from redis.asyncio import Redis
import os, json
import hashlib
import time
import cbor2


def unixtime():
    return time.time()


def get_config():
    with open(os.environ["HYBRIDOCR_CONFIG_FILE"], "r") as fd:
        config = json.loads(fd.read())
    config["production"] = config["webserver"].get("production", False)
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
        password=config["redis"]["auth"]["password"],
        encoding="utf-8",
        db=config["redis"]["db"],
    )


from google.cloud import vision
from google.auth import default

def google_ocr(image) -> AnnotateImageResponse:
    cred, proj = default()
    client = vision.ImageAnnotatorClient(credentials=cred)
    img = vision.Image(content=image)
    return client.text_detection(image=img)

def to_cbor(data):
    return cbor2.dumps(data)


def from_cbor(data):
    return cbor2.loads(data)


def compute_hash(data):
    return hashlib.sha256(data).digest()


