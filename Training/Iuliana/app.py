from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from http import HTTPStatus

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
            "username": self.username,
            "fullname": self.fullname,
            "email": self.email
        }


# Route for obtaining users using their username
@app.route("/users/username=<username>", methods=["GET"])
def get_user_by_username(username):
    found_user = db.session.query(User).filter(User.username == username).first()
    return jsonify(found_user.as_dict()), HTTPStatus.OK


# Route for obtaining users using their id
@app.route("/users/id=<user_id>", methods=["GET"])
def get_user_by_id(user_id):
    found_user = db.session.query(User).filter(User.id == user_id).first()
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


if __name__ == '__main__':
    db.create_all()  # Creates the necessary tables for the declared classes (User)
    db.session.commit()
    app.run("0.0.0.0", 5000)
