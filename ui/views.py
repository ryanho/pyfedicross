import httpx
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from .forms import FediverseLoginForm, NewPostForm
from django.views.decorators.csrf import csrf_exempt
from .libcrosspost import crosspost
from accounts.models import SocialNetwork, FediverseApp, User
from .social_login import social_logout, social_login
from django.core.exceptions import PermissionDenied
from .fediverse_login import FediverseLogin
import json
from .tasks import post_to_plurk
from .forms import WebhookSecretForm
import re


# Create your views here.


def home(request):
    action = '.'
    user = User.objects.get(id=request.user.id)
    if user.app.webhook_secret:
        context = {'webhook_is_set': True}
    else:
        context = {'webhook_is_set': False}

    if request.user.is_authenticated:
        sa = request.user.socialaccount_set.all()
        social_network = {
            'plurk': sa.filter(social_network=SocialNetwork.PLURK)
        }
        if request.method == 'POST':
            form = NewPostForm(request.POST, request.FILES)
            files = request.FILES.getlist('attachment')
            if form.is_valid():
                crosspost(request, form.cleaned_data, files)
            else:
                context.update({'form': form, 'social_network': social_network})
                return render(request, 'home.html', context)
        form = NewPostForm()
        context.update({'form': form, 'social_network': social_network})
        return render(request, 'home.html', context)
    else:
        if request.method == 'POST':
            form = FediverseLoginForm(request.POST)
            if form.is_valid():
                instance = form.cleaned_data['instance']
                prefix = f'{request.scheme}://{request.META["HTTP_HOST"]}'
                auth = FediverseLogin(request, instance, prefix)
                try:
                    app = FediverseApp.objects.get(domain=instance)
                except FediverseApp.DoesNotExist:
                    try:
                        app = auth.create_app()
                    except httpx.ConnectError:
                        context.update({'form': form, 'action': action, 'alert': '網域名稱不存在'})
                        return render(request, 'home.html', context)

                url = auth.authorize()

                # 重導向使用者到oauth認證授權頁面
                request.session['instance'] = instance
                return HttpResponseRedirect(url)
            else:
                context.update({'form': form, 'action': action})
                return render(request, 'home.html', context)
        form = FediverseLoginForm()
        context.update({'form': form, 'action': action})
        return render(request, 'home.html', context)


def connect_social_network(request, provider_name):
    if not request.user.is_authenticated:
        raise PermissionDenied('login first!')
    redirect_uri = request.GET.get('redirect_uri', None)
    result = social_login(request, provider_name, redirect_uri)
    if result is True:
        return HttpResponseRedirect('/')
    elif result is not None:
        return HttpResponseRedirect(result)
    return HttpResponseNotFound()


def disconnect_social_network(request, provider_name):
    if not request.user.is_authenticated:
        raise PermissionDenied('login first!')
    result, err = social_logout(request, provider_name)
    if result:
        return HttpResponseRedirect('/')
    return HttpResponseNotFound()


def webhook_settings(request):
    if not request.user.is_authenticated:
        return redirect('/')

    user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        form = WebhookSecretForm(request.POST, instance=user.app)
        if form.is_valid():
            form.save()
    else:
        form = WebhookSecretForm(instance=user.app)
    return render(request, 'webhook_setings.html', {'form': form})


@csrf_exempt
def webhook(request):
    if request.method == 'POST' and request.content_type == 'application/json':
        try:
            secret = request.headers.get('X-Misskey-Hook-Secret')
        except KeyError:
            raise PermissionDenied('X-Misskey-Hook-Secret is empty')

        result = json.loads(request.body)
        user = get_object_or_404(User, app__software='misskey', app__webhook_secret=secret)

        if result['body']['note']['replyId'] is None and result['body']['note']['visibility'] == 'public':
            is_sensitive = False
            qualifier = 'says'
            if result['body']['note'].get('text', '') is None:
                content = ''
            else:
                content = re.sub(r'@\w+', '', result['body']['note'].get('text', ''))

            emojis = result['body']['note'].get('emojis', list())
            for name in emojis:
                content = content.replace(f':{name}:', f' {emojis[name]} ')

            if result['body']['note']['renoteId']:
                qualifier = 'shares'
                note_url = result['body']['note']['renote']['uri']
            else:
                note_url = f"{result['server']}/notes/{result['body']['note']['id']}"

            if result['body']['note']['cw']:
                content = result['body']['note']['cw'] + '\n' + content
                is_sensitive = True
            files = []
            if len(result['body']['note']['files']) > 0:
                files = [file['thumbnailUrl'] for file in result['body']['note']['files']]

            plurk = user.socialaccount_set.filter(social_network=SocialNetwork.PLURK)
            if plurk:
                post_to_plurk.send(plurk.values()[0], qualifier, content, files, note_url, is_sensitive)
        return HttpResponse('OK')
    else:
        return HttpResponse(status=405)
