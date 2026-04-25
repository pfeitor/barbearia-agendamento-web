from django.db import models


class NotificacaoLog(models.Model):
    """Registro de todas as notificações enviadas por e-mail."""

    class Tipo(models.TextChoices):
        CONFIRMACAO_SOLICITADA = "CONFIRMACAO_SOLICITADA", "Solicitação de Confirmação"
        LEMBRETE_DIA = "LEMBRETE_DIA", "Lembrete do Dia"

    class Status(models.TextChoices):
        ENVIADO = "ENVIADO", "Enviado"
        FALHOU = "FALHOU", "Falhou"

    agendamento = models.ForeignKey(
        "agendamentos.Agendamento",
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    destinatario = models.EmailField()
    status = models.CharField(max_length=10, choices=Status.choices)
    erro = models.TextField(blank=True, default="")
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificacao_log"
        ordering = ["-enviado_em"]
        verbose_name = "Log de Notificação"
        verbose_name_plural = "Logs de Notificações"

    def __str__(self):
        return (
            f"{self.get_tipo_display()} → {self.destinatario} "
            f"[{self.get_status_display()}] em {self.enviado_em:%d/%m/%Y %H:%M}"
        )
