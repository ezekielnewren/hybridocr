from pymongo import MongoClient
import redis

import os, json
import time


def unixtime():
    return time.time()


def get_config():
    with open(os.environ["HYBRIDOCR_CONFIG_FILE"], "r") as fd:
        config = json.loads(fd.read())
    config["production"] = config["flask"].get("production", False)
    return config


def open_database(config):
    client = MongoClient(
        host=config["mongodb"]["uri"],
        username=config["mongodb"]["username"],
        password=config["mongodb"]["password"],
    )

    db = client.get_database(config["mongodb"]["dbname"])
    col_log = db.get_collection("log")
    col_log.insert_one({"boot": unixtime()})
    return client, db


def open_redis(config):
    node = config["redis"]["node"][0]
    client = redis.Redis(
        host=node["host"],
        port=node["port"],
        password=config["redis"]["auth"]["password"],
    )
    client.set("test", "test")
    client.delete("test")
    return client
