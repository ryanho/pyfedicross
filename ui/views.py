from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from .forms import FediverseLoginForm, NewPostForm
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login
from .libcrosspost import crosspost
from accounts.models import SocialNetwork, FediverseApp
from .social_login import social_logout, social_login
from django.core.exceptions import PermissionDenied
from .fediverse_login import FediverseLogin

# Create your views here.


def home(request):
    action = '.'
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
                return render(request, 'home.html', {'form': form, 'social_network': social_network})
        form = NewPostForm()
        return render(request, 'home.html', {'form': form, 'social_network': social_network})
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
                    app = auth.get_app()

                url = auth.authorize()

                # 重導向使用者到oauth認證授權頁面
                request.session['instance'] = instance
                return HttpResponseRedirect(url)
            else:
                return render(request, 'login_form.html', {'form': form, 'action': action})
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
