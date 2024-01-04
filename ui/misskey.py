import httpx
import hashlib
from asgiref.sync import async_to_sync


class Misskey:
    def __init__(self, instance):
        self.instance = instance

    @async_to_sync
    async def get_session(self, app_secret):
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f'https://{self.instance}/api/auth/session/generate',
                json={'appSecret': app_secret}
            )
            data = r.json()
            return data

    @async_to_sync
    async def create_app(self, callback_url):
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f'https://{self.instance}/api/app/create',
                json={
                    'name': 'fedicross',
                    'description': 'fedicross is an crosspost tool for fediverse and social network',
                    'permission': ["write:notes", "write:drive"],
                    'callbackUrl': callback_url,
                }
            )
            data = r.json()
            app_secret = data['secret']

            data = self.get_session(app_secret)

            return {'client_secret': app_secret, 'client_id': data['token'], 'authorize_url': data['url'], 'detail': data}

    @async_to_sync
    async def user_authenticate(self, client_secret, client_id, callback_url, token):
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f'https://{self.instance}/api/auth/session/userkey',
                json={
                    'appSecret': client_secret,
                    'token': token
                }
            )
            data = r.json()
            access_token = f"{data['accessToken']}{client_secret}".encode('utf-8')

            i = hashlib.sha256(access_token).hexdigest()
            user = data['user']

            return {'access_token': i, 'username': f"{user['username']}@{self.instance}", 'avatar': user['avatarUrl'], 'detail': user}

