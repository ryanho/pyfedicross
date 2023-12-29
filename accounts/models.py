from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class FediverseApp(models.Model):
    domain = models.CharField('Domain', max_length=100, primary_key=True)
    software = models.CharField('Software', max_length=100)
    detail = models.JSONField('Detail')
    client_id = models.CharField('Client ID', max_length=255)
    client_secret = models.CharField('Client Secret', max_length=255)
    authorize_url = models.URLField('Authorize Url', max_length=500)

    class Meta:
        verbose_name = 'Fediverse application'

    def __str__(self):
        return self.domain


class User(AbstractUser):
    avatar = models.URLField('Avatar', blank=True)
    app = models.ForeignKey(FediverseApp, on_delete=models.SET_NULL, null=True, blank=True)
    access_token = models.CharField('Access Token', max_length=255, blank=True)


class SocialNetwork(models.TextChoices):
    PLURK = 'plurk', 'Plurk'
    FACEBOOK = 'facebook', 'Facebook'


class SocialAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    social_network = models.CharField('社群網路', max_length=10, choices=SocialNetwork.choices)
    oauth_token = models.CharField('Oauth token', max_length=100)
    oauth_token_secret = models.CharField('Oauth token secret', max_length=100)
    detail = models.JSONField('detail token info', default=dict, blank=True, null=True)
    pref = models.JSONField('pref', default=dict, blank=True, null=True)
    extra_data = models.JSONField('extra data', default=dict, blank=True, null=True)

    class Meta:
        verbose_name = '社群網站帳號'

    def __str__(self):
        return self.social_network


class ExpireToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    social_network = models.CharField('社群網路', max_length=10, choices=SocialNetwork.choices)
    oauth_token = models.CharField('Oauth token', max_length=100)
    oauth_token_secret = models.CharField('Oauth token secret', max_length=100)
    created = models.DateTimeField('失效時間', auto_now_add=True)

    class Meta:
        verbose_name = '已失效的社群網站帳號憑證'

    def __str__(self):
        return f'{self.user}: {self.social_network} {self.oauth_token}'
