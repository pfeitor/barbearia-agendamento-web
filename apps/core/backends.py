from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db import models
from apps.clientes.models import Cliente


class TelefoneBackend(BaseBackend):
    """
    Backend de autenticação customizado para login de cliente por telefone.
    
    Este backend não é usado diretamente no authenticate() padrão,
    mas sim nas views de login do cliente para manter sessão customizada.
    """
    
    def authenticate(self, request, telefone=None, **kwargs):
        """
        Autentica cliente por telefone.
        Retorna instância de Cliente se encontrado, None caso contrário.
        """
        if telefone is None:
            return None
            
        try:
            cliente = Cliente.objects.get(telefone=telefone)
            return cliente
        except Cliente.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        Retorna usuário pelo ID. Para este backend, retorna Cliente.
        """
        try:
            return Cliente.objects.get(pk=user_id)
        except Cliente.DoesNotExist:
            return None


class AdminEmailBackend(BaseBackend):
    """
    Backend de autenticação para administradores usando email como username.
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Autentica administrador por email e senha.
        """
        if email is None or password is None:
            return None
            
        UserModel = get_user_model()
        
        try:
            # Tenta encontrar usuário por email ou username
            user = UserModel.objects.filter(
                models.Q(email=email) | models.Q(username=email)
            ).filter(is_staff=True).first()
            
            if user and user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            pass
        
        return None
    
    def get_user(self, user_id):
        """
        Retorna usuário administrador pelo ID.
        """
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id, is_staff=True)
        except UserModel.DoesNotExist:
            return None
