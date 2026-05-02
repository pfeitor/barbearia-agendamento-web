from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db import DatabaseError


class AdminEmailBackend(BaseBackend):
    """Backend de autenticação para administradores (is_staff=True) por e-mail e senha."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(email=email, is_staff=True)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except (UserModel.DoesNotExist, DatabaseError):
            return None
