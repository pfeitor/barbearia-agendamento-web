from django.contrib import admin
from .models import Profissional


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "ativo", "created_at")
    list_filter = ("ativo",)
    search_fields = ("nome",)
