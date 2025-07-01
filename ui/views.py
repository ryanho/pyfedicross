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
from .forms import WebhookForm
import secrets
import re


# Create your views here.


def home(request):
    action = '.'

    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        if user.app.webhook_secret:
            context = {'webhook_is_set': True}
        else:
            context = {'webhook_is_set': False}

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
                        return render(request, 'home.html', {'form': form, 'action': action, 'alert': '網域名稱不存在'})

                url = auth.authorize()

                # 重導向使用者到oauth認證授權頁面
                request.session['instance'] = instance
                return HttpResponseRedirect(url)
            else:
                return render(request, 'home.html', {'form': form, 'action': action})
        form = FediverseLoginForm()
        return render(request, 'home.html', {'form': form, 'action': action})


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
    secret = user.app.webhook_secret
    if request.method == 'POST':
        form = WebhookForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['method'] == 'create':
                secret = secrets.token_urlsafe()
                user.app.webhook_secret = secret
                user.app.save()
            elif form.cleaned_data['method'] == 'delete':
                user.app.webhook_secret = ''
                user.app.save()
                secret = ''
    else:
        form = WebhookForm()
    return render(request, 'webhook_setings.html', {'form': form, 'secret': secret})


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
            content = result['body']['note']['text']
            note_url = f"{result['server']}/notes/{result['body']['note']['id']}"
            note_files = result['body']['note'].get('files', list())
            renote_id = result['body']['note']['renoteId']

            # 轉發或引用
            if renote_id:
                qualifier = 'shares'
                note_files += result['body']['note']['renote']['files']
                note_url = result['body']['note']['renote']['uri']
                # 如果是轉發但轉發的貼文沒有附件
                if content is None and len(note_files) == 0:
                    return HttpResponse('OK')

            if content is None:
                content = ''

            if content:
                mention_user = re.findall(r'@[\w.-]+(?:@[\w.-]+\.\w+)?', content)
                if mention_user:
                    for at_user in mention_user:
                        content = content.replace(at_user, f"[{at_user}]({result['server']}/{at_user})")

                raw_emojis = re.findall(r':[\w-]+:', content)
                if raw_emojis:
                    r = httpx.get(f"{result['server']}/api/emojis")
                    emojis = r.json()['emojis']
                    for raw in raw_emojis:
                        item = next(item for item in emojis if item["name"] == raw.strip(':'))
                        content = content.replace(raw, f' {item["url"]} ')

            if result['body']['note']['cw']:
                content = result['body']['note']['cw'] + '\n' + content
                is_sensitive = True

            files = []
            if len(note_files) > 0:
                for file in result['body']['note']['files']:
                    if is_sensitive is False and file['isSensitive'] is True:
                        is_sensitive = True
                    files.append(file['url'])

            plurk = user.socialaccount_set.filter(social_network=SocialNetwork.PLURK)
            if plurk:
                content = re.sub(r'\~\~(.*?)\~\~', lambda m: f"--{m.group(1)}--", content)
                lang = plurk[0].extra_data.get('default_lang', 'en')
                post_to_plurk.send(plurk.values()[0], qualifier, lang, content, files, note_url, is_sensitive)
        return HttpResponse('OK')
    else:
        return HttpResponse(status=405)
