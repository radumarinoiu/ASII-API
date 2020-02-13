import time
import requests

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient("mongodb://{}:{}@testmongo-service/admin".format("test", "test"))
db = client["test_db"]
coll = db["test_coll"]


app = Flask(__name__)
CORS(app)


@app.route("/test", methods=["GET"])
def test():
    resp = requests.get("http://testapp2-service:80/test")
    return jsonify({"response": "Service 2 Works!", "additional_data": resp.json()})


@app.route("/db-test", methods=["GET"])
def test_get():
    entry = coll.find_one({"_id": ObjectId(request.get_json()["object_id"])})
    entry["_id"] = str(entry["_id"])
    return jsonify({"response": "Service 1 Works!", "object": entry})


@app.route("/db-test", methods=["POST"])
def test_post():
    inserted_id = coll.insert_one({"creation_time": time.time()}).inserted_id
    return jsonify({"response": "Service 1 Works!", "inserted_id": str(inserted_id)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    app.debug = True
