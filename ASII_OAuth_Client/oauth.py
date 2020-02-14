from authlib.client import OAuthClient


class GitHub(OAuthClient):
    OAUTH_TYPE = '2.0'
    OAUTH_NAME = 'test_client'
    OAUTH_CONFIG = {
        'api_base_url': 'http://localhost:5000',
        'access_token_url': 'http://localhost:5000/oauth/token',
        'authorize_url': 'http://localhost:5000/oauth/authorize',
        'client_kwargs': {'scope': 'profile'},
    }

    def profile(self, **kwargs):
        resp = self.get('user', **kwargs)
        resp.raise_for_status()
        data = resp.json()
        params = {
            'sub': str(data['id']),
            'name': data['name'],
            'email': data.get('email'),
            'preferred_username': data['login'],
            'profile': data['html_url'],
            'picture': data['avatar_url'],
            'website': data.get('blog'),
        }

        # The email can be be None despite the scope being 'user:email'.
        # That is because a user can choose to make his/her email private.
        # If that is the case we get all the users emails regardless if private or note
        # and use the one he/she has marked as `primary`
        if params.get("email") is None:
            resp = self.get("user/emails", **kwargs)
            resp.raise_for_status()
            data = resp.json()
            params["email"] = next(email["email"] for email in data if email["primary"])

        return UserInfo(params)
