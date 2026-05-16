from django.contrib import admin
from .models import NotificacaoLog


@admin.register(NotificacaoLog)
class NotificacaoLogAdmin(admin.ModelAdmin):
    list_display = (
        "agendamento",
        "tipo",
        "destinatario",
        "status",
        "provider",
        "enviado_em",
    )
    list_filter = ("tipo", "status", "provider", "enviado_em")
    search_fields = ("destinatario", "agendamento__cliente__nome", "provider_message_id")
    readonly_fields = (
        "agendamento",
        "tipo",
        "destinatario",
        "status",
        "erro",
        "provider",
        "provider_message_id",
        "enviado_em",
    )
    ordering = ("-enviado_em",)

    def has_add_permission(self, request):
        # Logs são criados apenas pelo sistema, não manualmente
        return False

    def has_change_permission(self, request, obj=None):
        return False
