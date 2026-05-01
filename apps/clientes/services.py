import random
import string
from datetime import timedelta

from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class AuthService:
    MAX_TENTATIVAS_HORA = 3
    EXPIRACAO_CODIGO_MINUTOS = 15

    @staticmethod
    def gerar_e_enviar_codigo(cliente_user):
        """Gera código de 6 dígitos, invalida anteriores e envia por e-mail.
        Levanta ValueError se o rate limit (3/hora) for atingido.
        """
        from .models import VerificacaoEmail
        from apps.notificacoes.services import NotificacaoService

        uma_hora_atras = timezone.now() - timedelta(hours=1)
        tentativas = VerificacaoEmail.objects.filter(
            cliente_user=cliente_user,
            created_at__gte=uma_hora_atras,
        ).count()

        if tentativas >= AuthService.MAX_TENTATIVAS_HORA:
            raise ValueError('Limite de tentativas atingido. Tente novamente em 1 hora.')

        VerificacaoEmail.objects.filter(
            cliente_user=cliente_user, is_used=False
        ).update(is_used=True)

        codigo = ''.join(random.choices(string.digits, k=6))
        expiracao = timezone.now() + timedelta(minutes=AuthService.EXPIRACAO_CODIGO_MINUTOS)

        VerificacaoEmail.objects.create(
            cliente_user=cliente_user,
            code=codigo,
            expires_at=expiracao,
        )

        NotificacaoService.enviar_email_verificacao(cliente_user, codigo)

    @staticmethod
    def verificar_codigo(cliente_user, codigo):
        """Marca o código como usado e ativa o ClienteUser. Retorna True se válido."""
        from .models import VerificacaoEmail

        try:
            verificacao = VerificacaoEmail.objects.get(
                cliente_user=cliente_user,
                code=codigo,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
        except VerificacaoEmail.DoesNotExist:
            return False

        verificacao.is_used = True
        verificacao.save(update_fields=['is_used'])

        cliente_user.is_active = True
        cliente_user.save(update_fields=['is_active'])

        return True

    @staticmethod
    def enviar_link_reset(cliente_user, request):
        """Gera token HMAC+timestamp e envia link de redefinição por e-mail.
        request é repassado para que a URL absoluta seja montada corretamente
        (http://127.0.0.1:8000 em dev, https://... em prod).
        """
        from apps.notificacoes.services import NotificacaoService

        uidb64 = urlsafe_base64_encode(force_bytes(cliente_user.pk))
        token = default_token_generator.make_token(cliente_user)
        NotificacaoService.enviar_email_reset_senha(cliente_user, uidb64, token, request)

    @staticmethod
    def validar_token_reset(uidb64, token):
        """Valida uidb64 + token (expira em 1h via PASSWORD_RESET_TIMEOUT).
        Retorna ClienteUser ou None.
        """
        from .models import ClienteUser

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = ClienteUser.objects.get(pk=uid)
        except (ClienteUser.DoesNotExist, ValueError, TypeError, OverflowError):
            return None

        if not default_token_generator.check_token(user, token):
            return None

        return user
