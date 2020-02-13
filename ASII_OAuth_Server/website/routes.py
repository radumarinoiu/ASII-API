import json
import time
import traceback

from flask import Blueprint, request, session
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from pbkdf2 import crypt
from .models import db, User, OAuth2Client
from .oauth2 import authorization, require_oauth


bp = Blueprint(__name__, 'home')


def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@bp.route("/", methods=["GET"])
def home():
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
        return render_template("home.html", user=user, clients=clients)
    else:
        return redirect("login")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password2 = request.form.get("password2")
        email = request.form.get("email")
        if len(password) < 8:
            return redirect("/")
        if password != password2:
            return redirect("/")
        user = User(
            username=username,
            password=crypt(password),
            email=email
        )
        db.session.add(user)
        db.session.commit()
        session['id'] = user.id
        return redirect('/')
    return render_template('register.html')


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user:
            if user.check_password(password):
                session['id'] = user.id
                return redirect('/')
            else:
                print("Wrong password")
        else:
            print("Wrong username")
    return render_template('login.html')


@bp.route('/logout')
def logout():
    del session['id']
    return redirect('/')


# THIS IS A CLIENT (SERVICE) NOT A USER
@bp.route('/create_client', methods=['GET', 'POST'])
def create_client():
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        return render_template('create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )

    if client.token_endpoint_auth_method == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)
    db.session.add(client)
    db.session.commit()
    return redirect('/')


# GET
# http://localhost:5000/oauth/authorize?grant_type=authorization_code&response_type=code&scope=profile&state=asdfgh&client_id=trm4mcCRFXNjeDVnkS1sl9Zm
# POST
# http://callback_uri?code=HpLvmJLoCtHEQTErwLbmaerm0P3ejiW9kLFbEYPh4OR8NS5Q&state=asdfgh
@bp.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            print(traceback.format_exc())
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


@bp.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')


@bp.route('/test', methods=['POST'])
def test():
    print("Test:", json.dumps(request.json()))
    return jsonify({})


@bp.route('/api/me')
@require_oauth('profile')
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username, email=user.email)
