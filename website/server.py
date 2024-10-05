from flask import Flask, request, render_template
from pymongo import MongoClient
import time
import os
import json




def unixtime():
    return time.time()


client = MongoClient(
    host=config["mongodb"]["uri"],
    username=config["mongodb"]["username"],
    password=config["mongodb"]["password"],
)

db = client.get_database(config["mongodb"]["dbname"])
col_log = db.get_collection("log")
col_log.insert_one({"boot": unixtime()})


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html',
                           production=production,
                           gtag_id=config["flask"]["gtag_id"],
                           )


@app.route('/register')
def register():
    return render_template('register.html',
                           production=production,
                           gtag_id=config["flask"]["gtag_id"],
                           )


@app.route('/about')
def about():
    return render_template('about.html',
                           production=production,
                           gtag_id=config["flask"]["gtag_id"],
                           )


@app.route('/save-email', methods=['POST'])
def save_email():
    body = json.loads(request.data)
    body["timestamp"] = unixtime()
    col_analytics = db.get_collection("analytics")
    col_analytics.insert_one(body)
    return json.dumps({"result": "ok"})


if __name__ == "__main__":
    app.run(port=config["flask"]["port"], debug=True)
