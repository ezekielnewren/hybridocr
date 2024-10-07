from flask import Flask, request, render_template

import time
import os
import json

from website import common

config = common.get_config()
client, db = common.open_database(config)
rd = common.open_redis(config)

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html',
                           production=config["production"],
                           gtag_id=config["flask"]["gtag_id"],
                           )


@app.route('/register')
def register():
    return render_template('register.html',
                           production=config["production"],
                           gtag_id=config["flask"]["gtag_id"],
                           )


@app.route('/about')
def about():
    return render_template('about.html',
                           production=config["production"],
                           gtag_id=config["flask"]["gtag_id"],
                           )


@app.route('/save-email', methods=['POST'])
def save_email():
    body = json.loads(request.data)
    body["timestamp"] = common.unixtime()
    col_analytics = db.get_collection("analytics")
    col_analytics.insert_one(body)
    return json.dumps({"result": "ok"})


if __name__ == "__main__":
    app.run(port=config["flask"]["port"], debug=True)
