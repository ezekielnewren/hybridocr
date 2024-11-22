from google.cloud.vision_v1 import AnnotateImageResponse
from pymongo import WriteConcern, ReadPreference
from pymongo.read_concern import ReadConcern
from redis.asyncio import Redis
from datetime import datetime, timezone
import os, json
import secrets
import hashlib
import time
import cbor2


DOMAIN = "hybridocr.com"


def unixtime():
    return time.time()


def open_database(config):
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(
        host=config["mongodb"]["uri"],
        username=config["mongodb"]["username"],
        password=config["mongodb"]["password"],
        w="majority",
        journal=True
    )

    db = client.get_database(
        config["mongodb"]["dbname"],
        write_concern=WriteConcern("majority"),
        read_concern=ReadConcern("majority"),
        read_preference=ReadPreference.PRIMARY
    )
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

def generate_alphanumeric(count):
    import string
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(count))


def new_cas():
    return secrets.randbits(63)


def year_month_str(t: float):
    dt = datetime.fromtimestamp(t, tz=timezone.utc)
    return str(dt.year)+str(dt.month).zfill(2)


def year_month_range(t: float):
    dt = datetime.fromtimestamp(t, tz=timezone.utc)
    y, m = dt.year, dt.month
    start = datetime(y, m, 1, 0, 0, 0, tzinfo=timezone.utc)
    if dt.month == 12:
        y, m = y+1, 1
    else:
        m += 1
    end = datetime(y, m, 1, 0, 0, 0, tzinfo=timezone.utc)
    return start.timestamp(), end.timestamp()
