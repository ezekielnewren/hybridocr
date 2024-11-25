from bson import ObjectId
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


def str2ObjectId(_id):
    if _id is None:
        return None
    elif isinstance(_id, ObjectId):
        return _id
    return ObjectId(bytes.fromhex(_id))


def ObjectId2str(_id: ObjectId):
    if _id is None:
        raise TypeError("ObjectId cannot be None")
    if not isinstance(_id, ObjectId):
        raise TypeError("_id must be an ObjectId")
    return str(_id)

def redis_auto_cast(data: dict, cast_keys=True, cast_values_to_int=True, cast_values_to_float=True, cast_values_to_str=True):
    if cast_keys:
        for k in list(data.keys()):
            if not isinstance(k, bytes):
                continue
            try:
                data[str(k, "utf-8")] = data[k]
                del data[k]
            except UnicodeDecodeError:
                pass

    for k, v in data.items():
        if cast_values_to_int and isinstance(v, bytes):
            try:
                data[k] = int(v)
                continue
            except ValueError:
                pass
        if cast_values_to_float and isinstance(v, bytes):
            try:
                data[k] = float(v)
                continue
            except ValueError:
                pass
        if cast_values_to_str and isinstance(v, bytes):
            try:
                data[k] = str(v, "utf-8")
                continue
            except UnicodeDecodeError:
                pass
    return data
