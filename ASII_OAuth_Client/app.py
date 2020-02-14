from flask import Flask, Blueprint, jsonify, redirect, request, session
from flask_cors import CORS
from flasgger import Swagger

from ASII_OAuth_Client.oauth_handler_bp import routes as oauth_routes

app = Flask(__name__)
app.secret_key = b"d3bb70b12e5ba50c62858652906adaeb"
CORS(app)
Swagger(app)

if __name__ == '__main__':
    oauth_bp = oauth_routes.setup_blueprint(
        client_id="E6pp6lW6u2Xd7V8P10pLceEU",
        client_secret="qJMis0FqnFW3hzdnDix1XBPxjUqrgWDwMYt1lQaJ91N0ET9K",
        scopes=["profile"],
        authorization_uri="http://localhost:5000/oauth/authorize",
        access_token_uri="http://localhost:5000/oauth/token"
    )
    app.register_blueprint(oauth_bp)
    app.run("0.0.0.0", 5001)
