from website.app import create_app, mail, environ

if __name__ == '__main__':
    app = create_app({
        'SECRET_KEY': '7f09e5d8de5529701af97c5b637b445b',
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:////db/db.sqlite',
    })
    # Email configurations
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = environ.get('EMAIL_PASS')
    mail.init_app(app)

    app.run("0.0.0.0", 5000)
