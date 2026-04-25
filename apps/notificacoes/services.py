"""Serviço de notificações por e-mail para o sistema de agendamentos."""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificacaoService:
    """Responsável por enviar e-mails de notificação e registrar os logs."""

    # ─── Ponto de entrada: criação de agendamento ─────────────────────────────

    @staticmethod
    def enviar_confirmacao_agendamento(agendamento):
        """
        Envia e-mail de confirmação de recebimento quando o agendamento
        é criado com status AGENDADO.
        """
        NotificacaoService._enviar_email(
            agendamento=agendamento,
            tipo="CONFIRMACAO_SOLICITADA",
            subject=f"✅ Agendamento recebido — {settings.BARBEARIA_NOME}",
            template="notificacoes/email_confirmacao_agendamento.html",
        )

    # ─── Ponto de entrada: lembrete do dia ────────────────────────────────────

    @staticmethod
    def enviar_lembrete_dia(agendamento):
        """
        Envia e-mail de lembrete no dia do agendamento.
        Chamado pelo management command `enviar_lembretes`.
        """
        NotificacaoService._enviar_email(
            agendamento=agendamento,
            tipo="LEMBRETE_DIA",
            subject=f"⏰ Lembrete: você tem um agendamento hoje — {settings.BARBEARIA_NOME}",
            template="notificacoes/email_lembrete_dia.html",
        )

    # ─── Lógica central ───────────────────────────────────────────────────────

    @staticmethod
    def _enviar_email(agendamento, tipo, subject, template):
        """
        Renderiza o template, envia o e-mail via SMTP e registra o resultado
        em NotificacaoLog.
        """
        from apps.notificacoes.models import NotificacaoLog

        destinatario = agendamento.cliente.email

        context = {
            "agendamento": agendamento,
            "barbearia_nome": settings.BARBEARIA_NOME,
            "cliente_nome": agendamento.cliente.nome,
            "profissional_nome": agendamento.profissional.nome,
            "servico_nome": agendamento.servico.nome,
            "data_hora": timezone.localtime(agendamento.data_hora_inicio),
        }

        try:
            html_body = render_to_string(template, context)
            # Versão texto puro como fallback
            text_body = (
                f"Olá, {context['cliente_nome']}!\n\n"
                f"Barbearia: {context['barbearia_nome']}\n"
                f"Serviço: {context['servico_nome']}\n"
                f"Profissional: {context['profissional_nome']}\n"
                f"Data/Hora: {context['data_hora']:%d/%m/%Y às %H:%M}\n"
            )

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinatario],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)

            NotificacaoLog.objects.create(
                agendamento=agendamento,
                tipo=tipo,
                destinatario=destinatario,
                status="ENVIADO",
            )
            logger.info(
                "Notificação [%s] enviada para %s (agendamento #%s)",
                tipo, destinatario, agendamento.pk,
            )

        except Exception as exc:
            erro_msg = str(exc)
            NotificacaoLog.objects.create(
                agendamento=agendamento,
                tipo=tipo,
                destinatario=destinatario,
                status="FALHOU",
                erro=erro_msg,
            )
            logger.error(
                "Falha ao enviar notificação [%s] para %s (agendamento #%s): %s",
                tipo, destinatario, agendamento.pk, erro_msg,
            )
