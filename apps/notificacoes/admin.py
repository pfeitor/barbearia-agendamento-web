from django.contrib import admin
from .models import NotificacaoLog


@admin.register(NotificacaoLog)
class NotificacaoLogAdmin(admin.ModelAdmin):
    list_display = (
        "agendamento",
        "tipo",
        "destinatario",
        "status",
        "enviado_em",
    )
    list_filter = ("tipo", "status", "enviado_em")
    search_fields = ("destinatario", "agendamento__cliente__nome")
    readonly_fields = (
        "agendamento",
        "tipo",
        "destinatario",
        "status",
        "erro",
        "enviado_em",
    )
    ordering = ("-enviado_em",)

    def has_add_permission(self, request):
        # Logs são criados apenas pelo sistema, não manualmente
        return False

    def has_change_permission(self, request, obj=None):
        return False
