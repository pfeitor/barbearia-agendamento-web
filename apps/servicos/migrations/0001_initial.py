from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Servico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                ("duracao_minutos", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("preco", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
            ],
            options={"db_table": "servico", "ordering": ["nome"]},
        ),
    ]
