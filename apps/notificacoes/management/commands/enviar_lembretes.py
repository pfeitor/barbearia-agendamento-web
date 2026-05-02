"""Management command para enviar lembretes de agendamentos com link de confirmação."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.agendamentos.models import Agendamento
from apps.agendamentos.services import ConfirmacaoLinkService
from apps.notificacoes.services import NotificacaoService


class Command(BaseCommand):
    help = "Envia e-mails de lembrete com link de confirmação para agendamentos futuros."

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        site_url = settings.SITE_URL.rstrip("/")
        intervalos = settings.LEMBRETE_DIAS_ANTECEDENCIA

        total_enviados = 0
        total_falhas = 0

        for dias in intervalos:
            data_alvo = hoje + timedelta(days=dias)
            agendamentos = Agendamento.objects.filter(
                data_hora_inicio__date=data_alvo,
                status=Agendamento.Status.AGENDADO,
            ).select_related("cliente", "profissional", "servico")

            count = agendamentos.count()
            if count == 0:
                self.stdout.write(
                    f"[D-{dias} | {data_alvo}] Nenhum agendamento pendente."
                )
                continue

            self.stdout.write(
                f"[D-{dias} | {data_alvo}] {count} agendamento(s) — enviando lembretes..."
            )

            for agendamento in agendamentos:
                try:
                    token_obj = ConfirmacaoLinkService.obter_ou_criar_token(agendamento)
                    link_base = f"{site_url}/agendamentos/responder/{token_obj.token}/"
                    NotificacaoService.enviar_lembrete_com_link(
                        agendamento,
                        link_confirmar=link_base + "?acao=CONFIRMADO",
                        link_cancelar=link_base + "?acao=CANCELADO",
                        dias_para_agendamento=dias,
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Lembrete enviado → {agendamento.cliente.email} "
                        f"(agendamento #{agendamento.pk} às "
                        f"{timezone.localtime(agendamento.data_hora_inicio):%H:%M})"
                    ))
                    total_enviados += 1
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(
                        f"  ✗ Falha ao enviar para {agendamento.cliente.email}: {exc}"
                    ))
                    total_falhas += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Concluído: {total_enviados} enviado(s), {total_falhas} falha(s)."
        ))
