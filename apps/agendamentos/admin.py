from django.contrib import admin
from .models import Agendamento


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "profissional", "servico", "data_hora_inicio", "status", "confirmado_whatsapp")
    list_filter = ("status", "confirmado_whatsapp", "profissional")
    search_fields = ("cliente__nome", "profissional__nome", "servico__nome")
