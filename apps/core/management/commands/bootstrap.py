import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db.utils import OperationalError, ProgrammingError


class Command(BaseCommand):
    help = "Aplica migrations e garante um superusuário inicial."

    def handle(self, *args, **options):
        self.stdout.write("Aplicando migrations...")
        call_command("migrate", interactive=False)

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Variáveis de superusuário não definidas. Pulando criação do admin."
                )
            )
            return

        User = get_user_model()

        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.SUCCESS(f"Superusuário '{username}' já existe.")
                )
                return

            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superusuário '{username}' criado com sucesso.")
            )
        except (OperationalError, ProgrammingError) as exc:
            self.stderr.write(self.style.ERROR(f"Erro ao criar superusuário: {exc}"))