import sys
import types
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.agendamentos.models import Agendamento
from apps.clientes.models import Cliente
from apps.notificacoes.models import NotificacaoLog
from apps.notificacoes.providers import BrevoEmailProvider, EmailSendResult, sanitize_provider_error
from apps.notificacoes.services import NotificacaoService
from apps.profissionais.models import Profissional
from apps.servicos.models import Servico


class BrevoEmailProviderTests(SimpleTestCase):
    def _fake_brevo_modules(self):
        sib_module = types.ModuleType("sib_api_v3_sdk")
        rest_module = types.ModuleType("sib_api_v3_sdk.rest")

        class ApiException(Exception):
            pass

        class SendSmtpEmail:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        sib_module.SendSmtpEmail = SendSmtpEmail
        rest_module.ApiException = ApiException
        return sib_module, rest_module, ApiException

    @override_settings(
        API_KEY_BREVO="xkeysib-secret",
        BREVO_SENDER_NAME="Minha Barbearia",
        BREVO_SENDER_EMAIL="noreply@example.com",
        BREVO_TIMEOUT=10,
    )
    def test_brevo_provider_builds_transactional_payload(self):
        sib_module, rest_module, _ = self._fake_brevo_modules()
        api_instance = Mock()
        api_instance.send_transac_email.return_value = types.SimpleNamespace(message_id="msg-123")

        with patch.dict(sys.modules, {"sib_api_v3_sdk": sib_module, "sib_api_v3_sdk.rest": rest_module}):
            result = BrevoEmailProvider(api_instance=api_instance).send(
                to_email="cliente@example.com",
                to_name="Cliente",
                subject="Assunto",
                html_body="<p>HTML</p>",
                text_body="Texto",
            )

        self.assertTrue(result.success)
        self.assertEqual(result.provider, "brevo")
        self.assertEqual(result.message_id, "msg-123")
        payload = api_instance.send_transac_email.call_args.args[0].kwargs
        self.assertEqual(payload["sender"], {"name": "Minha Barbearia", "email": "noreply@example.com"})
        self.assertEqual(payload["to"], [{"email": "cliente@example.com", "name": "Cliente"}])
        self.assertEqual(payload["subject"], "Assunto")
        self.assertEqual(payload["html_content"], "<p>HTML</p>")
        self.assertEqual(payload["text_content"], "Texto")

    @override_settings(API_KEY_BREVO="xkeysib-secret")
    def test_brevo_provider_returns_controlled_failure_for_api_exception(self):
        sib_module, rest_module, api_exception = self._fake_brevo_modules()
        api_instance = Mock()
        api_instance.send_transac_email.side_effect = api_exception("401 xkeysib-secret")

        with patch.dict(sys.modules, {"sib_api_v3_sdk": sib_module, "sib_api_v3_sdk.rest": rest_module}):
            result = BrevoEmailProvider(api_instance=api_instance).send(
                to_email="cliente@example.com",
                to_name="Cliente",
                subject="Assunto",
                html_body="<p>HTML</p>",
                text_body="Texto",
            )

        self.assertFalse(result.success)
        self.assertEqual(result.provider, "brevo")
        self.assertNotIn("xkeysib-secret", result.error)

    @override_settings(API_KEY_BREVO="xkeysib-secret")
    def test_sanitize_provider_error_masks_brevo_api_key(self):
        self.assertEqual(sanitize_provider_error("erro xkeysib-secret"), "erro [BREVO_API_KEY]")


class NotificacaoServiceTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Cliente Teste",
            telefone="11999990000",
            email="cliente@example.com",
        )
        self.profissional = Profissional.objects.create(nome="Profissional Teste")
        self.servico = Servico.objects.create(nome="Corte", duracao_minutos=30)
        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            profissional=self.profissional,
            servico=self.servico,
            data_hora_inicio=timezone.now() + timezone.timedelta(days=1),
            status=Agendamento.Status.AGENDADO,
        )
        NotificacaoLog.objects.all().delete()

    @override_settings(BARBEARIA_NOME="Minha Barbearia")
    def test_confirmacao_agendamento_logs_success_with_provider_message_id(self):
        provider = Mock()
        provider.send.return_value = EmailSendResult(
            success=True,
            provider="brevo",
            message_id="msg-123",
        )

        with patch("apps.notificacoes.services.get_email_provider", return_value=provider):
            NotificacaoService.enviar_confirmacao_agendamento(self.agendamento)

        log = NotificacaoLog.objects.get()
        self.assertEqual(log.status, "ENVIADO")
        self.assertEqual(log.provider, "brevo")
        self.assertEqual(log.provider_message_id, "msg-123")
        self.assertEqual(log.tipo, "CONFIRMACAO_SOLICITADA")
        provider.send.assert_called_once()

    def test_provider_failure_logs_failure_without_raising_for_agendamento(self):
        provider = Mock()
        provider.send.return_value = EmailSendResult(
            success=False,
            provider="brevo",
            error="Falha controlada",
        )

        with patch("apps.notificacoes.services.get_email_provider", return_value=provider):
            NotificacaoService.enviar_lembrete_dia(self.agendamento)

        log = NotificacaoLog.objects.get()
        self.assertEqual(log.status, "FALHOU")
        self.assertEqual(log.provider, "brevo")
        self.assertEqual(log.erro, "Falha controlada")
