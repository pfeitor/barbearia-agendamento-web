"""Servico de notificacoes por e-mail para o sistema de agendamentos."""

import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apps.notificacoes.providers import get_email_provider

logger = logging.getLogger(__name__)


class NotificacaoService:
    """Responsavel por enviar e-mails de notificacao e registrar os logs."""

    @staticmethod
    def enviar_confirmacao_agendamento(agendamento):
        """Envia e-mail de confirmacao quando o agendamento e criado."""
        NotificacaoService._enviar_email(
            agendamento=agendamento,
            tipo="CONFIRMACAO_SOLICITADA",
            subject=f"\u2705 Agendamento recebido \u2014 {settings.BARBEARIA_NOME}",
            template="notificacoes/email_confirmacao_agendamento.html",
        )

    @staticmethod
    def enviar_lembrete_dia(agendamento):
        """Envia e-mail de lembrete no dia do agendamento."""
        NotificacaoService._enviar_email(
            agendamento=agendamento,
            tipo="LEMBRETE_DIA",
            subject=f"\u23f0 Lembrete: voc\u00ea tem um agendamento hoje \u2014 {settings.BARBEARIA_NOME}",
            template="notificacoes/email_lembrete_dia.html",
        )

    @staticmethod
    def enviar_lembrete_com_link(
        agendamento,
        link_confirmar,
        link_cancelar,
        dias_para_agendamento: int,
    ):
        """Envia lembrete ativo com links de confirmacao e cancelamento."""
        context = NotificacaoService._contexto_agendamento(agendamento)
        context.update(
            {
                "link_confirmar": link_confirmar,
                "link_cancelar": link_cancelar,
                "dias_para_agendamento": dias_para_agendamento,
            }
        )

        if dias_para_agendamento == 0:
            subject = f"\u23f0 Seu agendamento \u00e9 hoje \u2014 {settings.BARBEARIA_NOME}"
        else:
            subject = (
                f"\U0001f5d3\ufe0f Lembrete: agendamento em {dias_para_agendamento} dia(s) \u2014 "
                f"{settings.BARBEARIA_NOME}"
            )

        html_body = render_to_string("notificacoes/email_lembrete_com_link.html", context)
        text_body = (
            f"Ol\u00e1, {context['cliente_nome']}!\n\n"
            f"Confirmar: {link_confirmar}\n"
            f"Cancelar: {link_cancelar}\n"
        )

        NotificacaoService._enviar_email_renderizado(
            agendamento=agendamento,
            tipo="LEMBRETE_COM_LINK",
            destinatario=agendamento.cliente.email,
            destinatario_nome=agendamento.cliente.nome,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    @staticmethod
    def enviar_email_verificacao(cliente_user, codigo):
        """Envia codigo de verificacao de 6 digitos ao novo usuario."""
        context = {
            "email": cliente_user.email,
            "codigo": codigo,
            "barbearia_nome": settings.BARBEARIA_NOME,
        }
        html_body = render_to_string("notificacoes/email_verificacao.html", context)
        text_body = f"Seu c\u00f3digo de verifica\u00e7\u00e3o \u00e9: {codigo}\nExpira em 15 minutos."

        result = NotificacaoService._send_transactional_email(
            to_email=cliente_user.email,
            to_name=getattr(cliente_user, "email", ""),
            subject=f"Verifica\u00e7\u00e3o de e-mail \u2014 {settings.BARBEARIA_NOME}",
            html_body=html_body,
            text_body=text_body,
        )
        if not result.success:
            logger.error(
                "Falha ao enviar e-mail de verificacao para %s via %s: %s",
                cliente_user.email,
                result.provider,
                result.error,
            )
            raise RuntimeError(result.error)
        logger.info(
            "E-mail de verificacao enviado para %s via %s",
            cliente_user.email,
            result.provider,
        )

    @staticmethod
    def enviar_email_reset_senha(cliente_user, uidb64, token, request):
        """Envia link de redefinicao de senha."""
        path = f"/clientes/resetar-senha/{uidb64}/{token}/"
        link = request.build_absolute_uri(path)
        context = {
            "email": cliente_user.email,
            "link": link,
            "barbearia_nome": settings.BARBEARIA_NOME,
        }
        html_body = render_to_string("notificacoes/email_reset_senha.html", context)
        text_body = f"Redefina sua senha acessando: {link}\nExpira em 1 hora."

        result = NotificacaoService._send_transactional_email(
            to_email=cliente_user.email,
            to_name=getattr(cliente_user, "email", ""),
            subject=f"Redefinir senha \u2014 {settings.BARBEARIA_NOME}",
            html_body=html_body,
            text_body=text_body,
        )
        if not result.success:
            logger.error(
                "Falha ao enviar e-mail de reset para %s via %s: %s",
                cliente_user.email,
                result.provider,
                result.error,
            )
            raise RuntimeError(result.error)
        logger.info(
            "E-mail de reset enviado para %s via %s",
            cliente_user.email,
            result.provider,
        )

    @staticmethod
    def _enviar_email(agendamento, tipo, subject, template):
        context = NotificacaoService._contexto_agendamento(agendamento)
        html_body = render_to_string(template, context)
        text_body = (
            f"Ol\u00e1, {context['cliente_nome']}!\n\n"
            f"Barbearia: {context['barbearia_nome']}\n"
            f"Servi\u00e7o: {context['servico_nome']}\n"
            f"Profissional: {context['profissional_nome']}\n"
            f"Data/Hora: {context['data_hora']:%d/%m/%Y \u00e0s %H:%M}\n"
        )

        NotificacaoService._enviar_email_renderizado(
            agendamento=agendamento,
            tipo=tipo,
            destinatario=agendamento.cliente.email,
            destinatario_nome=agendamento.cliente.nome,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    @staticmethod
    def _enviar_email_renderizado(
        *,
        agendamento,
        tipo,
        destinatario,
        destinatario_nome,
        subject,
        html_body,
        text_body,
    ):
        from apps.notificacoes.models import NotificacaoLog

        result = NotificacaoService._send_transactional_email(
            to_email=destinatario,
            to_name=destinatario_nome,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        status = "ENVIADO" if result.success else "FALHOU"
        NotificacaoLog.objects.create(
            agendamento=agendamento,
            tipo=tipo,
            destinatario=destinatario,
            status=status,
            erro="" if result.success else result.error,
            provider=result.provider,
            provider_message_id=result.message_id,
        )

        if result.success:
            logger.info(
                "Notificacao [%s] enviada para %s (agendamento #%s) via %s.",
                tipo,
                destinatario,
                agendamento.pk,
                result.provider,
            )
        else:
            logger.error(
                "Falha ao enviar notificacao [%s] para %s (agendamento #%s) via %s: %s",
                tipo,
                destinatario,
                agendamento.pk,
                result.provider,
                result.error,
            )

    @staticmethod
    def _send_transactional_email(*, to_email, to_name, subject, html_body, text_body):
        provider = get_email_provider()
        return provider.send(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    @staticmethod
    def _contexto_agendamento(agendamento):
        return {
            "agendamento": agendamento,
            "barbearia_nome": settings.BARBEARIA_NOME,
            "cliente_nome": agendamento.cliente.nome,
            "profissional_nome": agendamento.profissional.nome,
            "servico_nome": agendamento.servico.nome,
            "data_hora": timezone.localtime(agendamento.data_hora_inicio),
        }
