from django.contrib import admin
from .models import Profissional, ProfessionalSchedule


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "ativo", "created_at")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(ProfessionalSchedule)
class ProfessionalScheduleAdmin(admin.ModelAdmin):
    list_display = ("profissional", "get_weekday_display", "start_time", "end_time", "is_day_off")
    list_filter = ("weekday", "is_day_off", "profissional")
    search_fields = ("profissional__nome",)
    
    def get_weekday_display(self, obj):
        return obj.Weekday(obj.weekday).label
    get_weekday_display.short_description = "Dia da Semana"
    
    fieldsets = (
        ("Informações Básicas", {
            "fields": ("profissional", "weekday", "is_day_off")
        }),
        ("Horários de Trabalho", {
            "fields": ("start_time", "end_time"),
            "description": "Preencha apenas em dias de trabalho"
        }),
        ("Horário de Almoço", {
            "fields": ("lunch_start", "lunch_end"),
            "description": "Opcional - deixe em branco se não tiver almoço"
        }),
    )
