from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "telefone", "email", "created_at")
    search_fields = ("nome", "telefone", "email")
