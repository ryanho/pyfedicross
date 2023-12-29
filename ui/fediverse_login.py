import httpx
from accounts.models import FediverseApp
from .misskey import Misskey
from .mastodon import Mastodon
from django.contrib.auth import authenticate


class FediverseLogin:
    def __init__(self, request, instance, prefix=None):
        self.request = request
        self.instance = instance
        self.app = None
        self.scope = list()
        self.access_token = None
        self.prefix = prefix
        self.app = None
        self.software = None
        self.api = None

    def get_app(self):
        if self.app is None or self.app.software == 'misskey':
            app = self.create_app()
            self.app = app
        return self.app

    def create_app(self):
        self.software = self.check_instance()
        if self.software == 'misskey':
            self.api = Misskey(self.instance)
            objs = FediverseApp.objects.filter(software=self.software)
            if objs:
                self.app = objs[0]
                return self.app
            redirect_uri = f'{self.prefix}/callback/misskey/'
            result = self.api.create_app(redirect_uri)
        elif self.software == 'mastodon':
            self.api = Mastodon(self.instance)
            objs = FediverseApp.objects.filter(software=self.software)
            if objs:
                self.app = objs[0]
                return self.app
            redirect_uri = f'{self.prefix}/callback/mastodon/'
            result = self.api.create_app(redirect_uri)
        else:
            raise Exception('Not support software.')

        app = FediverseApp(
            domain=self.instance,
            software=self.software,
            detail=result['detail'],
            client_id=result['client_id'],
            client_secret=result['client_secret'],
            authorize_url=result['authorize_url'],
        )
        app.save()
        return app

    def authorize(self):
        app = self.get_app()
        if app.software == 'misskey':
            session = self.api.get_session(app.client_secret)
            return session['url']
        return app.authorize_url

    def authenticate(self, request, code, callback_url=None):
        app = self.get_app()
        auth_user = self.api.user_authenticate(app.client_secret, app.client_id, callback_url, code)
        user = authenticate(request, username=auth_user['username'], access_token=auth_user['access_token'],
                            app=app, avatar=auth_user['avatar'])
        return user

    def check_instance(self):
        r = httpx.get(f'https://{self.instance}/.well-known/nodeinfo')
        data = r.json()

        if len(data['links']) > 0:
            node_info = httpx.get(data['links'][0]['href'])
            self.software = node_info.json()['software']['name']

        return self.software
