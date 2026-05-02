import secrets

from django.db import models
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.profissionais.models import Profissional
from apps.servicos.models import Servico


class Agendamento(models.Model):
    class Status(models.TextChoices):
        AGENDADO = "AGENDADO", "Agendado"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        CANCELADO = "CANCELADO", "Cancelado"
        CONCLUIDO = "CONCLUIDO", "Concluído"

    data_hora_inicio = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGENDADO)
    confirmado_whatsapp = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="agendamentos")
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name="agendamentos")
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name="agendamentos")

    class Meta:
        db_table = "agendamento"
        ordering = ["data_hora_inicio"]
        indexes = [
            models.Index(fields=["data_hora_inicio"]),
            models.Index(fields=["status"]),
            models.Index(fields=["profissional", "data_hora_inicio"]),
        ]

    def __str__(self):
        return f"{self.cliente} - {self.servico} - {self.data_hora_inicio}"


class TokenConfirmacaoAgendamento(models.Model):
    agendamento = models.OneToOneField(
        Agendamento, on_delete=models.CASCADE, related_name="token_confirmacao"
    )
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    usado_em = models.DateTimeField(null=True, blank=True)
    acao = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[("CONFIRMADO", "Confirmado"), ("CANCELADO", "Cancelado")],
    )

    class Meta:
        db_table = "token_confirmacao_agendamento"

    def __str__(self):
        return f"Token agendamento #{self.agendamento_id} — {self.acao or 'pendente'}"
