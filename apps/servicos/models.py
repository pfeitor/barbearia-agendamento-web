from django.core.validators import MinValueValidator
from django.db import models


class Servico(models.Model):
    nome = models.CharField(max_length=100)
    duracao_minutos = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "servico"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
