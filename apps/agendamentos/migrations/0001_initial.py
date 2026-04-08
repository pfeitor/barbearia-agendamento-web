from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [("clientes", "0001_initial"), ("profissionais", "0001_initial"), ("servicos", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Agendamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data_hora_inicio", models.DateTimeField()),
                ("status", models.CharField(choices=[("AGENDADO", "Agendado"), ("CONFIRMADO", "Confirmado"), ("CANCELADO", "Cancelado"), ("CONCLUIDO", "Concluído")], default="AGENDADO", max_length=20)),
                ("confirmado_whatsapp", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("cliente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="agendamentos", to="clientes.cliente")),
                ("profissional", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="agendamentos", to="profissionais.profissional")),
                ("servico", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="agendamentos", to="servicos.servico")),
            ],
            options={"db_table": "agendamento", "ordering": ["data_hora_inicio"]},
        ),
        migrations.AddIndex(model_name="agendamento", index=models.Index(fields=["data_hora_inicio"], name="agendamento_data_ho_idx")),
        migrations.AddIndex(model_name="agendamento", index=models.Index(fields=["status"], name="agendamento_status_idx")),
        migrations.AddIndex(model_name="agendamento", index=models.Index(fields=["profissional", "data_hora_inicio"], name="agendamento_profiss_idx")),
    ]
