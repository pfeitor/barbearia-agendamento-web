from django.db import models
from django.utils import timezone


class Profissional(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "profissional"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
