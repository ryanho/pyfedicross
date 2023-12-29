from django.contrib.auth.backends import BaseBackend
from .models import User


class FediverseBackend(BaseBackend):
    def authenticate(self, request, username=None, access_token=None, app=None, avatar=None):
        if username is None or access_token is None or app is None:
            return

        try:
            user = User.objects.get(username=username)
            if user.access_token != access_token:
                user.access_token = access_token
                user.save()
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, access_token=access_token, app=app, avatar=avatar)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
