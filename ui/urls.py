from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    # path('callback/mastodon/', views.mstdn_authorize, name='mstdn_authorize'),
    path('social_login/<str:provider_name>/', views.connect_social_network, name='social_login'),
    path('social_logout/<str:provider_name>/', views.disconnect_social_network, name='social_logout'),
    path('webhook', views.webhook, name='webhook'),
    path('webhook_settings/', views.webhook_settings, name='webhook_settings'),
]
