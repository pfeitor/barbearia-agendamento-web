"""Management command para enviar lembretes de agendamentos do dia."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.agendamentos.models import Agendamento
from apps.notificacoes.services import NotificacaoService


class Command(BaseCommand):
    help = "Envia e-mails de lembrete para todos os agendamentos marcados para hoje."

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        agendamentos_hoje = Agendamento.objects.filter(
            data_hora_inicio__date=hoje,
            status__in=[Agendamento.Status.AGENDADO, Agendamento.Status.CONFIRMADO],
        ).select_related("cliente", "profissional", "servico")

        total = agendamentos_hoje.count()

        if total == 0:
            self.stdout.write(self.style.WARNING(
                f"[{hoje}] Nenhum agendamento encontrado para hoje."
            ))
            return

        self.stdout.write(f"[{hoje}] {total} agendamento(s) encontrado(s). Enviando lembretes...")

        enviados = 0
        falhas = 0

        for agendamento in agendamentos_hoje:
            try:
                NotificacaoService.enviar_lembrete_dia(agendamento)
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ Lembrete enviado → {agendamento.cliente.email} "
                    f"(agendamento #{agendamento.pk} às "
                    f"{timezone.localtime(agendamento.data_hora_inicio):%H:%M})"
                ))
                enviados += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Falha ao enviar para {agendamento.cliente.email}: {exc}"
                ))
                falhas += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Concluído: {enviados} enviado(s), {falhas} falha(s)."))
