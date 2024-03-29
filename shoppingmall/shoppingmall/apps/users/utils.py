from django.contrib.auth.backends import ModelBackend

from users.models import User


class MobileModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(mobile=username)
        except User.DoesNotExist:
            pass
        else:
            if user and user.check_password(password):
                return user
