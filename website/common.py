import base64

from google.cloud.vision_v1 import AnnotateImageResponse
from redis.asyncio import Redis
import os, json
import hashlib
import time
import cbor2
from pathlib import Path

from website.hcvault import VaultClient


def unixtime():
    return time.time()


def get_config():
    with open(os.environ["HYBRIDOCR_CONFIG_FILE"], "r") as fd:
        config = json.loads(fd.read())
    return config


async def get_full_config():
    config = get_config()
    vault = VaultClient(config["vault"]["VAULT_ADDR"], config["vault"]["VAULT_TOKEN"])

    result = await vault.read("auth/token/lookup-self")
    env = result["data"]["meta"]["env"]
    config = await vault.kv_get("kv/env/" + env)
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
    return json.dumps(json.loads(data), separators=(',', ':'))





def get_service_gmail(config):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    # SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    SCOPES = ["https://mail.google.com/"]
    parent = Path(os.environ["HYBRIDOCR_CONFIG_FILE"]).parent

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    file_token = parent/"token.json"
    file_cred = parent/"gmail2.json"
    if file_token.exists():
        creds = Credentials.from_authorized_user_file(str(file_token), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(file_cred), SCOPES
            )
            creds = flow.run_local_server(port=6324)
        # Save the credentials for the next run
        with open(file_token, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def list_email(config, inbox):
    service = get_service_gmail(config)

    results = service.users().messages().list(userId=inbox+"@hybridocr.com").execute()

    return results


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
