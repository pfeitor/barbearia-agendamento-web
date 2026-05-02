"""
Data migration: para cada Cliente existente que já possua e-mail mas ainda não
tenha um ClienteUser vinculado, cria um ClienteUser com is_active=True e senha
inutilizável (o cliente precisará usar 'Esqueci minha senha' para definir uma).

Relevante apenas para bancos de dados que passaram pela migração anterior ao
sistema de auth por e-mail (ex.: produção em Render).
"""

from django.db import migrations
from django.contrib.auth.hashers import make_password


def criar_cliente_users(apps, schema_editor):
    Cliente = apps.get_model('clientes', 'Cliente')
    ClienteUser = apps.get_model('clientes', 'ClienteUser')

    for cliente in Cliente.objects.filter(cliente_user__isnull=True, email__isnull=False):
        if not cliente.email:
            continue

        # Evita duplicatas caso o e-mail já exista em ClienteUser
        if ClienteUser.objects.filter(email=cliente.email).exists():
            cliente_user = ClienteUser.objects.get(email=cliente.email)
        else:
            cliente_user = ClienteUser(
                email=cliente.email,
                is_active=True,
                is_staff=False,
                # make_password(None) gera o marcador de senha inutilizável ('!...')
                # sem depender de métodos do modelo histórico
                password=make_password(None),
            )
            cliente_user.save()

        cliente.cliente_user = cliente_user
        cliente.save(update_fields=['cliente_user'])


def desfazer_criacao(apps, schema_editor):
    """Desfaz apenas os ClienteUser criados por esta migration (senha inutilizável)."""
    Cliente = apps.get_model('clientes', 'Cliente')
    ClienteUser = apps.get_model('clientes', 'ClienteUser')

    for cliente in Cliente.objects.filter(cliente_user__isnull=False):
        cu = cliente.cliente_user
        # Senha inutilizável começa com '!' — equivale a has_usable_password() = False
        if cu.password and cu.password.startswith('!'):
            cliente.cliente_user = None
            cliente.save(update_fields=['cliente_user'])
            cu.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('clientes', '0002_auth_email'),
    ]

    operations = [
        migrations.RunPython(criar_cliente_users, desfazer_criacao),
    ]
