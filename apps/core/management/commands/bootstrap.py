import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db.utils import OperationalError, ProgrammingError


class Command(BaseCommand):
    help = "Aplica migrations e garante um superusuário inicial (cria ou atualiza senha)."

    def handle(self, *args, **options):
        self.stdout.write("Aplicando migrations...")
        call_command("migrate", interactive=False)

        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_EMAIL ou DJANGO_SUPERUSER_PASSWORD não definidos. "
                    "Pulando gestão do admin."
                )
            )
            return

        User = get_user_model()

        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"is_staff": True, "is_superuser": True, "is_active": True},
            )
            user.set_password(password)
            if not user.is_staff:
                user.is_staff = True
            if not user.is_active:
                user.is_active = True
            user.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Superusuário '{email}' criado."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Senha do superusuário '{email}' atualizada."))
        except (OperationalError, ProgrammingError) as exc:
            self.stderr.write(self.style.ERROR(f"Erro ao gerir superusuário: {exc}"))
