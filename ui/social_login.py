from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect
from django.urls import reverse
import httpx
from django.core.cache import cache
from accounts.models import SocialAccount, FediverseApp, SocialNetwork
from authlib.integrations.httpx_client import OAuth1Client
from plurk_oauth import PlurkAPI


def plurk(request, redirect_uri=None):
    if redirect_uri is None:
        prefix = f'{request.scheme}://{request.META["HTTP_HOST"]}'
        redirect_uri = f'{prefix}{reverse("social_login", kwargs={"provider_name": "plurk"})}'
    if 'oauth_verifier' in request.GET:
        request_token = cache.get(request.GET.get('oauth_token'))
        oauth_token = request_token['oauth_token']
        oauth_token_secret = request_token['oauth_token_secret']
        client = OAuth1Client(
            settings.PLURK_CONSUMER_KEY,
            settings.PLURK_CONSUMER_SECRET,
            token=oauth_token,
            token_secret=oauth_token_secret
        )
        verifier = request.GET.get('oauth_verifier')
        access_token_url = 'https://www.plurk.com/OAuth/access_token'
        token = client.fetch_access_token(access_token_url, verifier)
        plurk_api = PlurkAPI(settings.PLURK_CONSUMER_KEY, settings.PLURK_CONSUMER_SECRET)
        plurk_api.authorize(token['oauth_token'], token['oauth_token_secret'])
        user_info = plurk_api.callAPI('/APP/Users/me')
        SocialAccount.objects.update_or_create(
            user=request.user, social_network=SocialNetwork.PLURK,
            defaults={
                'oauth_token': token['oauth_token'],
                'oauth_token_secret': token['oauth_token_secret'],
            },
            extra_data=user_info,
        )

        return True
    else:
        client = OAuth1Client(
            settings.PLURK_CONSUMER_KEY,
            settings.PLURK_CONSUMER_SECRET,
            redirect_uri=redirect_uri
        )
        request_token_url = 'https://www.plurk.com/OAuth/request_token'
        request_token = client.fetch_request_token(request_token_url)

        cache.set(request_token['oauth_token'], request_token)
        authenticate_url = 'https://www.plurk.com/OAuth/authorize'
        return client.create_authorization_url(authenticate_url)


def social_login(request, provider_name, redirect_uri=None):
    # plurk
    if provider_name == 'plurk':
        return plurk(request, redirect_uri)
    else:
        return None


def social_logout(request, provider_name):
    if provider_name == 'plurk':
        access_token = request.user.socialaccount_set.get(social_network=SocialNetwork.PLURK)
        client = OAuth1Client(
            settings.PLURK_CONSUMER_KEY,
            settings.PLURK_CONSUMER_SECRET,
            token=access_token.oauth_token,
            token_secret=access_token.oauth_token_secret,
        )
        expire_token_url = 'https://www.plurk.com/APP/expireToken'
        resp = client.get(expire_token_url)
        access_token.delete()
        return True, resp.text
    else:
        return None


