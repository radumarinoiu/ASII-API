import requests

from secrets import token_hex
from flask import current_app as app, Blueprint, jsonify, redirect, request, session

oauth_bp = None
app_data = {}


def setup_blueprint(client_id, client_secret, scopes, authorization_uri, access_token_uri):
    global app_data, oauth_bp
    app_data = {
        "authorization_uri": authorization_uri,
        "access_token_uri": access_token_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": " ".join(scopes),
        "grant_type": "authorization_code",
        "response_type": "code"
    }
    oauth_bp = Blueprint("oauth_handler_bp", __name__)
    return oauth_bp


@oauth_bp.route("/authorize", methods=["GET"])
def login():
    # access_token = session.get("access_token")
    # if access_token:
    #     resp = requests.get(app_data["api_url"], headers={"Authorization": "Bearer {}".format(access_token)})
    #     if resp.status_code == 200:
    #         return jsonify(resp.json())
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


# http://localhost:5001/auth_callback?code=1d4H3fYjnJnHgUIlHnQnKAKKqYivhzoTpgqhuYJSFf1oDulg&state=asdfgh
@oauth_bp.route("/auth_callback", methods=["GET"])
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
    resp = requests.get(app_data["api_url"], headers={"Authorization": "Bearer {}".format(access_token)})
    return jsonify(resp.json())
