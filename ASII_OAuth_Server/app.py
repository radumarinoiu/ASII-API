from website.app import create_app

if __name__ == '__main__':
    app = create_app({
        'SECRET_KEY': 'secret',
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite',
    })
    app.run("0.0.0.0", 5000)
