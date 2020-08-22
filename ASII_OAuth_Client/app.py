import logging
import time
from http import HTTPStatus
from secrets import token_hex

import requests
from flask import Flask, Blueprint, jsonify, redirect, request, session, render_template
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = b"d3bb70b12e5ba50c62858652906adaeb"
CORS(app)
app_data = {}


def setup(client_id, client_secret, scopes, authorization_uri, access_token_uri):
    global app_data
    app_data = {
        "authorization_uri": authorization_uri,
        "access_token_uri": access_token_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": " ".join(scopes),
        "grant_type": "authorization_code",
        "response_type": "code",
        "api_url": "http://localhost:5000/"
    }


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


def get_user_data(url):
    access_token = session.get("access_token")
    if access_token:
        resp = requests.get(app_data["api_url"] + url, headers={"Authorization": "Bearer {}".format(access_token)})
        if resp.status_code == 200:
            return resp.json()
    return None


@app.route("/profile_basic", methods=["GET"])
def get_basic_profile():
    user_data = get_user_data("/api/me")
    if user_data is not None:
        return render_template("profile.html", profile_data=user_data)
    if time.time() - session.get("access_token_time", 0) < 5:
        return jsonify({"err": "Permission denied!"}), HTTPStatus.UNAUTHORIZED
    session["next_url"] = "/profile_basic"
    return redirect("/authorize")


@app.route("/profile", methods=["GET"])
def get_profile():
    user_data = get_user_data("/profile")
    if user_data is not None:
        return render_template("profile.html", profile_data=user_data)
    if time.time() - session.get("access_token_time", 0) < 5:
        return jsonify({"err": "Permission denied!"}), HTTPStatus.UNAUTHORIZED
    session["next_url"] = "/profile"
    return redirect("/authorize")


@app.route("/member", methods=["GET"])
def get_member_data():
    user_data = get_user_data("/members")
    if user_data is not None:
        return render_template("error.html", error=user_data)
    if time.time() - session.get("access_token_time", 0) < 5:
        return jsonify({"err": "Permission denied!"}), HTTPStatus.UNAUTHORIZED
    session["next_url"] = "/member"
    return redirect("/authorize")


@app.route("/authorize", methods=["GET"])
def authorize():
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
            scope=app_data["scopes"],
            state=state_val
        ))


# http://127.0.0.1:5001/auth_callback?code=1d4H3fYjnJnHgUIlHnQnKAKKqYivhzoTpgqhuYJSFf1oDulg&state=asdfgh
@app.route("/auth_callback", methods=["GET"])
def auth_callback():
    """
    Callback route for after authorization.

    parameters:
        - name: code
        in: args
        type: string
        required: true
        description: Authorization code sent by OAuth Server
        - name: state
        in: args
        type: string
        required: true
        description: State value sent by us to the OAuth Server, then sent back by it to check authenticity
    responses:
        401:
            description: State mismatch, a sign of a possible man-in-the-middle attack!
        500:
            description: An internal error occured, please contact the developer.
        200:
            description: Ok
    """
    authorization_code = request.args.get("code")
    state_val = request.args.get("state")
    if state_val != session.get("state_val"):
        return "Wrong state value. This could be a Man-in-the-middle attack!", 401
    resp = requests.post(app_data["access_token_uri"],
                         data={
                             "grant_type": "authorization_code",
                             "scope": "profile",
                             "code": authorization_code},
                         auth=(
                             app_data["client_id"], app_data["client_secret"]))
    access_token = resp.json().get("access_token")
    session["access_token"] = access_token
    session["access_token_time"] = time.time()
    next_url = session.pop("next_url", "/")
    # try:
    #     resp = requests.get(request.url_root + next_url)
    #     if resp.status_code != 200:
    #         logging.error("Permission denied for resource [{}]".format(request.url_root + next_url))
    #         return render_template("error.html", error="Permission denied for resource [{}]".format(request.url_root + next_url))
    # except Exception:
    #     logging.exception("Failed to access resource [{}]".format(request.url_root + next_url))
    #     return render_template("error.html", error="Failed to access resource [{}]".format(request.url_root + next_url))
    return redirect(next_url)


if __name__ == '__main__':
    setup(
        client_id="LEVyjBkKu4g0q2fqGWsxsTAi",
        client_secret="veHQSPugf701fx6CkP88hRXVkMfF8xwtMAEWSTl0WiS45zGg",
        scopes="profile profile_read asii_members_read fiipractic".split(" "),
        authorization_uri="http://localhost:5000/oauth/authorize",
        access_token_uri="http://localhost:5000/oauth/token"
    )
    app.run("0.0.0.0", 5001)
