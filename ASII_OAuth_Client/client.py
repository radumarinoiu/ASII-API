from flask import Flask
from flask_cors import CORS
from authlib.flask.client import OAuth
from loginpass import create_flask_blueprint, GitHub

app = Flask(__name__)
CORS(app)
oauth = OAuth(app)


def handle_authorize(remote, token, user_info):
    if token:
        print(remote.name, token)
    if user_info:
        print(user_info)
        return ""
    raise Exception("Invalid")


if __name__ == '__main__':
    github_bp = create_flask_blueprint(GitHub, oauth, handle_authorize)
    app.register_blueprint(github_bp, url_prefix='/github')
    app.run("0.0.0.0", 5000)
