import httpx


class Mastodon:
    def __init__(self, instance):
        self.instance = instance

    def create_app(self, callback_url):
        r = httpx.post(
            f'https://{self.instance}/api/v1/apps',
            json={
                'client_name': 'fedicross',
                'redirect_uris': callback_url,
                'scopes': 'read:accounts write:statuses write:media'
            }
        )
        data = r.json()
        r.close()

        client_secret = data['client_secret']
        client_id = data['client_id']

        url = (f'https://{self.instance}/oauth/authorize?client_id={client_id}'
               f'&scope=read:accounts+write:statuses+write:media&response_type=code'
               f'&redirect_uri={callback_url}')

        return {'client_secret': client_secret, 'client_id': client_id, 'authorize_url': url, 'detail': data}

    def user_authenticate(self, client_secret, client_id, callback_url, code):
        r = httpx.post(
            f'https://{self.instance}/oauth/token',
            json={
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': callback_url,
                'grant_type': 'authorization_code',
                'code': code,
                'scope': 'read:accounts write:statuses write:media'
            }
        )
        data = r.json()
        access_token = data['access_token']

        r = httpx.get(
            f'https://{self.instance}/api/v1/accounts/verify_credentials',
            headers={
                'Authorization': f'Bearer {access_token}'
            }
        )
        data = r.json()
        return {'access_token': access_token, 'username': f"{data['username']}@{self.instance}",
                'avatar': data['avatar'], 'detail': data}
