from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from http import HTTPStatus

import requests

app = Flask(__name__)
app.secret_key = b"q3w35g223523g52v32"  # Random string, generat o singura data per aplicatie
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Baza de date e salvata in memorie, nu pe disk
CORS(app)
db = SQLAlchemy(app)


class User(db.Model):
    # Declare the table to use for this model (class)
    __tablename__ = "users"

    # Declare the columns for the 'users' table
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String, nullable=False)
    fullname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)

    # Method for providing a string based on user info
    def __repr__(self):
        return "<User(username={}, fullname={}, email={})>".format(self.username, self.fullname, self.email)

    # Method for providing a dictionary based on user info
    def as_dict(self):
        return {
            "user_id": self.id,
            "username": self.username,
            "fullname": self.fullname,
            "email": self.email
        }


class CreditCard(db.Model):
    __tablename__ = "cards"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    card_number = db.Column(db.String, nullable=False)
    funds = db.Column(db.Numeric(10, 2), nullable=False)
    id_owner = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return "<CreditCard(card_number={},funds={},id_owner={})>".format(self.card_number, self.funds, self.id_owner)

    def as_dict(self):
        return{
            "id": self.id,
            "card_number": self.card_number,
            "funds": self.funds,
            "id_owner": self.id_owner
        }


# Route for obtaining users using their username
@app.route("/users/username=<username>", methods=["GET"])
def get_user_by_username(username):
    found_user = db.session.query(User).filter(User.username == username).first()
    if not found_user:
        return jsonify({"err": "User not found!"}), HTTPStatus.NOT_FOUND
    return jsonify(found_user.as_dict()), HTTPStatus.OK


# Route for obtaining users using their id
@app.route("/users/id=<user_id>", methods=["GET"])
def get_user_by_id(user_id):
    found_user = db.session.query(User).filter(User.id == user_id).first()
    if not found_user:
        return jsonify({"err": "User not found!"}), HTTPStatus.NOT_FOUND
    return jsonify(found_user.as_dict()), HTTPStatus.OK


# Route for creating new users
@app.route("/users", methods=["POST"])
def post_user():
    if not request.is_json:
        return jsonify({"err": "No JSON content received."}), HTTPStatus.BAD_REQUEST
    user_data = request.get_json()
    new_user = User(
        username=user_data.get("username", None),
        fullname=user_data.get("fullname", None),
        email=user_data.get("email", None)
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.as_dict()), HTTPStatus.CREATED


@app.route("/credit_cards", methods=["POST"])
def post_card():
    if not request.is_json:
        return jsonify({"err": "No JSON content received."}), HTTPStatus.BAD_REQUEST
    card_data = request.get_json()
    new_card = CreditCard(
        card_number=card_data.get("card_number"),
        funds=card_data.get("funds"),
        id_owner=card_data.get("id_owner")
    )
    db.session.add(new_card)
    db.session.commit()
    return jsonify(new_card.as_dict()), HTTPStatus.CREATED


@app.route("/credit_cards/add_funds/card_number=<credit_card_number>", methods=["PUT"])
def add_funds(credit_card_number, value):
    found_card = db.session.query(CreditCard).filter(CreditCard.card_number == credit_card_number).first()
    if not found_card:
        return jsonify({"err": "Card not found!"}), HTTPStatus.NOT_FOUND
    else:
        CreditCard.funds = CreditCard.funds + float(value)


@app.route("/credit_cards/take_funds/card_number=<credit_card_number>", methods=["PUT"])
def take_funds(credit_card_number, value):
    found_card = db.session.query(CreditCard).filter(CreditCard.card_number == credit_card_number).first()
    if not found_card:
        return jsonify({"err": "Card not found!"}), HTTPStatus.NOT_FOUND
    else:
        CreditCard.funds = CreditCard.funds + float(value)


@app.route("/credit_cards/card_number=<credit_card_number>", methods=["GET"])
def get_credit_card_by_number(credit_card_number):
    found_card = db.session.query(CreditCard).filter(CreditCard.card_number == credit_card_number).first()
    if not found_card:
        return jsonify({"err": "Card not found!"}), HTTPStatus.NOT_FOUND
    return jsonify(found_card.as_dict()), HTTPStatus.OK


@app.route("/credit_cards/id_owner=<owner>", methods=["GET"])
def get_credit_card_by_id_owner(owner):
    found_card = db.session.query(CreditCard).filter(CreditCard.id_owner == owner).first()
    if not found_card:
        return jsonify({"err": "Card not found!"}), HTTPStatus.NOT_FOUND
    return jsonify(found_card.as_dict()), HTTPStatus.OK


@app.route("/credit_cards/transfer", methods=["PATCH"])
def transfer():
    if not request.is_json:
        return jsonify({"err": "No JSON content received."}), HTTPStatus.NOT_FOUND
    data = request.get_json()
    card_number_1 = data["card1"]
    card_number_2 = data["card2"]
    amount = data["amount"]
    # resp = requests.get("http://localhost:5002/credit_cards/card_number={}".format(card1))
    # if resp.status_code != HTTPStatus.OK:
    #     return jsonify({"err": "Failed getting card1"}), resp.status_code
    card1 = db.session.query(CreditCard).filter(CreditCard.card_number == card_number_1).first()
    card2 = db.session.query(CreditCard).filter(CreditCard.card_number == card_number_2).first()
    if card1.funds < amount:
        return jsonify({"err": "Not enough funds to make the transfer!"}), HTTPStatus.BAD_REQUEST
    card1.funds -= amount
    card2.funds += amount
    db.session.commit()


if __name__ == '__main__':
    db.create_all()  # Creates the necessary tables for the declared classes (User)
    db.session.commit()
    app.run("0.0.0.0", 5002)
