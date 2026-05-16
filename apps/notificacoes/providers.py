"""Providers de e-mail transacional."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

logger = logging.getLogger(__name__)


@dataclass
class EmailSendResult:
    success: bool
    provider: str
    message_id: str = ""
    error: str = ""
    raw_response: str = ""


class EmailProvider:
    provider_name = "base"

    def send(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str = "",
    ) -> EmailSendResult:
        raise NotImplementedError


class DjangoEmailProvider(EmailProvider):
    provider_name = "smtp"

    def __init__(self, *, backend: str | None = None, provider_name: str = "smtp"):
        self.backend = backend
        self.provider_name = provider_name

    def send(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str = "",
    ) -> EmailSendResult:
        try:
            connection = get_connection(backend=self.backend) if self.backend else None
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body or "",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
                connection=connection,
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
            return EmailSendResult(success=True, provider=self.provider_name)
        except Exception as exc:
            return EmailSendResult(
                success=False,
                provider=self.provider_name,
                error=sanitize_provider_error(exc),
            )


class BrevoEmailProvider(EmailProvider):
    provider_name = "brevo"

    def __init__(self, api_instance: Any | None = None):
        self.api_instance = api_instance

    def _get_api_instance(self):
        if self.api_instance is not None:
            return self.api_instance

        import sib_api_v3_sdk

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.API_KEY_BREVO
        configuration.timeout = settings.BREVO_TIMEOUT
        api_client = sib_api_v3_sdk.ApiClient(configuration)
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
        return self.api_instance

    def send(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        text_body: str = "",
    ) -> EmailSendResult:
        try:
            import sib_api_v3_sdk
            from sib_api_v3_sdk.rest import ApiException

            send_email = sib_api_v3_sdk.SendSmtpEmail(
                sender={
                    "name": settings.BREVO_SENDER_NAME,
                    "email": settings.BREVO_SENDER_EMAIL,
                },
                to=[{"email": to_email, "name": to_name or to_email}],
                subject=subject,
                html_content=html_body,
                text_content=text_body or None,
            )
            response = self._get_api_instance().send_transac_email(send_email)
            message_id = getattr(response, "message_id", "") or getattr(response, "messageId", "")
            return EmailSendResult(
                success=True,
                provider=self.provider_name,
                message_id=message_id or "",
                raw_response=summarize_response(response),
            )
        except ImportError as exc:
            logger.exception("SDK da Brevo nao esta instalado.")
            return EmailSendResult(
                success=False,
                provider=self.provider_name,
                error=sanitize_provider_error(exc),
            )
        except ApiException as exc:
            logger.warning(
                "Falha controlada na API Brevo para %s: %s",
                to_email,
                sanitize_provider_error(exc),
            )
            return EmailSendResult(
                success=False,
                provider=self.provider_name,
                error=sanitize_provider_error(exc),
                raw_response=summarize_response(exc),
            )
        except Exception as exc:
            logger.exception("Falha inesperada no envio Brevo para %s.", to_email)
            return EmailSendResult(
                success=False,
                provider=self.provider_name,
                error=sanitize_provider_error(exc),
            )


def get_email_provider() -> EmailProvider:
    if settings.EMAIL_PROVIDER == "brevo":
        if settings.API_KEY_BREVO:
            return BrevoEmailProvider()
        if settings.DEBUG:
            return DjangoEmailProvider(
                backend="django.core.mail.backends.console.EmailBackend",
                provider_name="brevo-console",
            )
    return DjangoEmailProvider()


def summarize_response(response: Any) -> str:
    value = repr(response)
    return sanitize_provider_error(value[:500])


def sanitize_provider_error(error: Any) -> str:
    value = str(error)
    api_key = getattr(settings, "API_KEY_BREVO", "")
    if api_key:
        value = value.replace(api_key, "[BREVO_API_KEY]")
    value = re.sub(r"xkeysib-[A-Za-z0-9._-]+", "xkeysib-[redacted]", value)
    return value
