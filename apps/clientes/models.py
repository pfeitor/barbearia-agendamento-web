from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cliente"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
