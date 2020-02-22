from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
import requests  # A nu se confunda cu request de la flask

from http import HTTPStatus

app = Flask(__name__)

# Random string, generat o singura data per aplicatie
app.secret_key = b"4sv4v64vsvws64"
CORS(app)

users_api_uri = "http://localhost:5002/users"


class User(object):
    def __init__(self, username, fullname, email, user_id=None):
        self.user_id = user_id
        self.username = username
        self.fullname = fullname
        self.email = email

    # Method for providing a string based on user info
    def __repr__(self):
        return "<User(username={}, fullname={}, email={})>".format(
            self.username, self.fullname, self.email)

    # Method for creating a user object based on a user dictionary
    @staticmethod
    def from_dict(user_as_dict):
        # This will raise an EXCEPTION if the user_as_dict does not contain all
        # the required fields
        return User(
            username=user_as_dict["username"],
            fullname=user_as_dict["fullname"],
            email=user_as_dict["email"],
            user_id=user_as_dict.get("user_id")
        )

    # Method for providing a dictionary based on user info
    def as_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "fullname": self.fullname,
            "email": self.email
        }


# Route for obtaining users using their username
@app.route("/username=<username>", methods=["GET"])
def get_user_by_username(username):
    resp = requests.get(
        "{}/username={}".format(users_api_uri, username))
    if resp.status_code == HTTPStatus.OK:
        try:
            found_user = User.from_dict(resp.json())
        except KeyError:
            return jsonify("Invalid user data received from called API!"),\
                   HTTPStatus.FAILED_DEPENDENCY
        return jsonify(found_user.as_dict()), HTTPStatus.OK
    else:
        return resp.content, resp.status_code


# Route for obtaining users using their id
@app.route("/id=<user_id>", methods=["GET"])
def get_user_by_id(user_id):
    resp = requests.get(
        "{}/id={}".format(users_api_uri, user_id))
    if resp.status_code == HTTPStatus.OK:
        try:
            found_user = User.from_dict(resp.json())
        except KeyError:
            return jsonify("Invalid user data received from called API!"),\
                   HTTPStatus.FAILED_DEPENDENCY
        return jsonify(found_user.as_dict()), HTTPStatus.OK
    else:
        return resp.content, resp.status_code


# Route for creating new users
@app.route("/", methods=["POST"])
def post_user():
    if not request.is_json:
        return jsonify({"err": "No JSON content received."}),\
               HTTPStatus.BAD_REQUEST
    user_data = request.get_json()
    try:
        new_user = User(
            username=user_data["username"],
            fullname=user_data["fullname"],
            email=user_data["email"]
        )
    except KeyError:
        return jsonify("Invalid user data received in request!"),\
               HTTPStatus.BAD_REQUEST
    resp = requests.post(
        "{}".format(users_api_uri), json=new_user.as_dict())
    if resp.status_code == HTTPStatus.CREATED:
        return jsonify(resp.json()), resp.status_code
    else:
        return resp.content, resp.status_code


@app.route("/<from_currency>_to_<to_currency>")
def get_exchange_rate(from_currency, to_currency):
    """Get the exchange rate from the currency of the first parameter to the
     currency of the second parameter."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    exchange_api = "https://api.exchangeratesapi.io/latest?base={}".format(
        from_currency)

    # Verify that the first currency is correct
    response = requests.get(exchange_api)
    if response.status_code == HTTPStatus.BAD_REQUEST:
        return jsonify("Unknown currency: {}".format(from_currency)), \
               HTTPStatus.BAD_REQUEST

    if response.status_code == HTTPStatus.OK:
        to_json = response.json()
        try:
            return jsonify({"value": to_json["rates"][to_currency],
                            "from": "{}".format(from_currency),
                            "to": to_currency}), HTTPStatus.OK
        except KeyError:    # The second currency isn't correct
            return jsonify("Unknown currency: {}".format(to_currency)),\
                   HTTPStatus.BAD_REQUEST
    else:
        return jsonify("Something went really wrong!"),\
               response.status_code


if __name__ == '__main__':
    app.run("0.0.0.0", 5003)
