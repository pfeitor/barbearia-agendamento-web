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
