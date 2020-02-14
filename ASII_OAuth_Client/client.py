from secrets import token_hex

import requests

from flask import Flask, jsonify, redirect, request, url_for, session
from flask_cors import CORS
from authlib.flask.client import OAuth
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
app.secret_key = b"bf9712u,!b3g97gb121t@1h123h"
CORS(app)
oauth = OAuth(app)

app_data = {
    "name": "test_client",
    "authorization_uri": "http://localhost:5000/oauth/authorize",
    "token_uri": "http://localhost:5000/oauth/token",
    "api_url": "http://localhost:5000/api/me",
    "client_id": "E6pp6lW6u2Xd7V8P10pLceEU",
    "client_secret": "qJMis0FqnFW3hzdnDix1XBPxjUqrgWDwMYt1lQaJ91N0ET9K",
    "scope": "profile",
    "grant_type": "authorization_code",
    "response_type": "code"
}


@app.route("/authorize", methods=["GET"])
def login():
    requested_scopes = request.get_json().get("scopes")
    access_token = session.get("access_token")
    if access_token:
        resp = requests.get(app_data["api_url"], headers={"Authorization": "Bearer {}".format(access_token)})
        if resp.status_code == 200:
            return jsonify(resp.json())
    state_val = token_hex(16)
    session["state_val"] = state_val
    return redirect(
        "{url}?client_id={client_id}&"
        "grant_type={grant_type}&"
        "response_type={response_type}&"
        "scope={scope}&"
        "state={state}".format(
            url=app_data["authorization_uri"],
            client_id=app_data["client_id"],
            grant_type=app_data["grant_type"],
            response_type=app_data["response_type"],
            scope=" ".join(requested_scopes),
            state=state_val
        ))


# http://localhost:5001/auth_callback?code=1d4H3fYjnJnHgUIlHnQnKAKKqYivhzoTpgqhuYJSFf1oDulg&state=asdfgh
@app.route("/auth_callback", methods=["GET"])
def auth_callback():
    authorization_code = request.args.get("code")
    state_val = request.args.get("state")
    if state_val != session.get("state_val"):
        return "Wrong state value. This could be a Man-in-the-middle attack!", 401
    resp = requests.post(app_data["token_uri"],
                         data={
                             "grant_type": "authorization_code",
                             "scope": "profile",
                             "code": authorization_code},
                         auth=(
                             app_data["client_id"], app_data["client_secret"]))
    access_token = resp.json().get("access_token")
    session["access_token"] = access_token
    resp = requests.get(app_data["api_url"], headers={"Authorization": "Bearer {}".format(access_token)})
    return jsonify(resp.json())


@app.route("/profile", methods=["GET"])
def get_profile():
    return jsonify({})


if __name__ == '__main__':
    app.run("0.0.0.0", 5001)
