from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notificacoes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificacaolog",
            name="provider",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="notificacaolog",
            name="provider_message_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
