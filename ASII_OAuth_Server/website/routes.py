import json
import time
import traceback
from httpstatus import HTTPStatus

from flask import Blueprint, request, session, url_for
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from pbkdf2 import crypt
from .models import db, User, OAuth2Client
from .oauth2 import authorization, require_oauth
from .mailer import mail, Message

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


@bp.route("/register", methods=["POST"])
def register():
    password = request.form.get("password")
    password2 = request.form.get("password2")
    email = request.form.get("email")
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    # phone = request.form.get("phone")
    # profile_photo = request.form.get("profilePhoto")
    # role = request.form.get("role")
    # departament = request.form.get("departament")

    if len(password) < 8:
        return redirect("/")
    if password != password2:
        return redirect("/")

    user = User(
        password=crypt(password),
        email=email,
        firstname=firstname,
        lastname=lastname,
        verified=False,  # By default    =>  you should validate the user!
        # asii_members_data={
        #     "profilePhoto": profile_photo,
        #     "role": role,
        #     "departament": departament
        # }
    )

    db.session.add(user)
    db.session.commit()
    session['id'] = user.id
    return redirect('/')


@bp.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = User.query.filter_by(email=email).first()
    if user:
        if user.check_password(password):
            session['id'] = user.id
            return redirect('/')
        else:
            print("Wrong password")
    else:
        print("Wrong email")


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
    if not user and 'email' in request.form:
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
    if request.form['confirm']:
        # print(request.form['confirm'], user)
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
    return jsonify({"test": "test"}), HTTPStatus.OK


@bp.route('/api/me')
@require_oauth('profile')
def api_me():
    user = current_token.user
    return jsonify(id=user.id, email=user.email), HTTPStatus.OK


#
# NEW ROUTES ADDED
#


@bp.route('/profile/', methods=['GET'])
@require_oauth('profile_read')
def profile_read():
    """Return profile data in form of JSON."""
    user = current_token.user
    return jsonify(
        {
            "email": user.email,
            "id": user.id,
            "password": user.password,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "verified": user.verified
        }
    ), HTTPStatus.OK


@bp.route('/members/', methods=['GET'])
@require_oauth('asii_members_read')
def members_read():
    """Return just the data specific to an ASII member."""
    user = current_token.user
    return jsonify(({
        'profilePhoto': user.asii_members_data['profilePhoto'],
        'role': user.asii_members_data['role'],
        'departament':  user.asii_members_data['departament']
    })), HTTPStatus.OK


@bp.route('/members/', methods=['PUT'])
@require_oauth('asii_members_write')
def members_write():
    """Update ASII member's data into database."""
    if request.is_json:
        user = current_token.user
        data = request.get_json()

        updated_data = {
            'profilePhoto': data.get('profilePhoto'),
            'role': data.get('role'),
            'departament': data.get('departament')
        }

        obj = User.query.filter_by(id=user.id).first()
        obj.asii_members_data = updated_data
        db.session.commit()

        return jsonify(({
            'profilePhoto': user.asii_members_data['profilePhoto'],
            'role': user.asii_members_data['role'],
            'departament': user.asii_members_data['departament']
        })), HTTPStatus.OK
    else:
        return jsonify({"err": "No JSON content received."}), HTTPStatus.BAD_REQUEST


def send_reset_email(user):
    """Send an email containing a link to reset the password of the user."""
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='no-reply@asii.ro',  # Modify the sender field with your email
                  recipients=[user.email])

    # If the recipient doesn't support html-rendered email, this will be sent
    msg.body = """\
Hello, {}!
To reset your password, visit the following link:
{}

If you did not intend to receive this email, you can safely ignore it.
(c) ASII 2020""".format(user.firstname, url_for('website.routes.reset_token', token=token, _external=True))

    # Sent if the sender supports html-rendered email
    msg.html = render_template('email.html', token=url_for('website.routes.reset_token', token=token, _external=True),
                               username=user.firstname)
    mail.send(msg)
    

@bp.route('/reset_password/', methods=['POST'])
def reset_request():
    """Handle the password-reset process. Call send_reset_email() if all good."""
    # If the user is logged in, send them to homepage
    if current_user():
        return redirect("/")

    email = request.form.get("email")
    user = User.query.filter_by(email=email).first()

    # If that email is not registered, send the user to the register page
    # Ii spui sa astepte pana maine -- 201, 404
    if user is None:
        return jsonify({"err": "No user is registered with that email address."}), HTTPStatus.BAD_REQUEST

    send_reset_email(user)
    return redirect('/login')


@bp.route('/reset_password/<token>', methods=['POST'])
def reset_token(token):
    """Reset the password using the token from the link received in the password-reset email."""
    # If the user is logged in, send them to homepage
    if current_user():
        return redirect("/")

    # Check the token for authenticity
    user = User.verify_reset_token(token)
    if user is None:
        return jsonify({'err': 'This is an invalid or expired token.'}), HTTPStatus.BAD_REQUEST

    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    if password1 != password2:
        return render_template('reset_password.html')
    elif password1 is None:
        return render_template('reset_password.html')

    user.password = crypt(password1)     # update user's password into database
    db.session.commit()
    return redirect('/login')
    # return render_template('reset_password.html')
