from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout, login
from ui.fediverse_login import FediverseLogin
# Create your views here.


def mylogout(request: HttpRequest) -> HttpResponse:
    logout(request)
    next_url = request.GET.get('next', None)
    if next_url:
        return HttpResponseRedirect(next_url)
    else:
        return HttpResponseRedirect('/')


def misskey_callback(request: HttpRequest) -> HttpResponse:
    token = request.GET.get('token', None)
    if token is None:
        return HttpResponseRedirect('/')

    prefix = f'{request.scheme}://{request.META["HTTP_HOST"]}'
    redirect_uri = f'{prefix}/callback/misskey/'
    instance = request.session['instance']
    f = FediverseLogin(request, instance)
    user = f.authenticate(request, token, redirect_uri)
    login(request, user)
    return HttpResponseRedirect('/')


def mastodon_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET.get('code', None)
    if code is None:
        return HttpResponseRedirect('/')

    prefix = f'{request.scheme}://{request.META["HTTP_HOST"]}'
    redirect_uri = f'{prefix}/callback/mastodon/'
    instance = request.session['instance']
    f = FediverseLogin(request, instance)
    user = f.authenticate(request, code, redirect_uri)
    login(request, user)
    return HttpResponseRedirect('/')
