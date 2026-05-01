from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager


class ClienteUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser deve ter is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser deve ter is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class ClienteUser(AbstractUser):
    username = None
    email = models.EmailField('e-mail', unique=True)
    is_active = models.BooleanField('ativo', default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = ClienteUserManager()

    class Meta:
        db_table = 'cliente_user'
        verbose_name = 'usuário cliente'
        verbose_name_plural = 'usuários clientes'

    def __str__(self):
        return self.email


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    cliente_user = models.OneToOneField(
        ClienteUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='perfil',
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cliente"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class VerificacaoEmail(models.Model):
    cliente_user = models.ForeignKey(
        ClienteUser,
        on_delete=models.CASCADE,
        related_name='verificacoes',
    )
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'verificacao_email'
        ordering = ['-created_at']

    def __str__(self):
        return f"Verificação {self.code} para {self.cliente_user.email}"

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()
