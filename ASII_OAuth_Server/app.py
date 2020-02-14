from website.app import create_app

if __name__ == '__main__':
    app = create_app({
        'SECRET_KEY': '7f09e5d8de5529701af97c5b637b445b',
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite',
    })
    app.run("0.0.0.0", 5000)
