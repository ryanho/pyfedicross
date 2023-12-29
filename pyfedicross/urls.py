"""
URL configuration for pyfedicross project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from accounts.views import mylogout as logout
from accounts.views import misskey_callback, mastodon_callback
from ui.social_login import plurk

urlpatterns = [
    path('super/', admin.site.urls),
    path('', include('ui.urls')),
    path('logout/', logout, name='logout'),
    path('callback/misskey/', misskey_callback, name='misskey_callback'),
    path('callback/mastodon/', mastodon_callback, name='mastodon_callback'),
    path('callback/plurk/', plurk, name='plurk_callback'),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
