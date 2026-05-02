"""
Garante que as tabelas do sistema de autenticação por e-mail existam.

- Instalações novas (dev): 0001_initial já criou tudo; este migration é no-op.
- Produção (banco legado): 0001_initial foi registrado com o schema antigo
  (só tabela 'cliente'). Este migration cria as tabelas que faltam sem tocar
  nos dados existentes.
"""

from django.db import migrations


def criar_tabelas_auth_se_necessario(apps, schema_editor):
    from django.db import connection

    tabelas = connection.introspection.table_names()

    # Cria ClienteUser (e suas tabelas M2M) somente se ainda não existe.
    if 'cliente_user' not in tabelas:
        ClienteUser = apps.get_model('clientes', 'ClienteUser')
        schema_editor.create_model(ClienteUser)

    # Cria VerificacaoEmail somente se ainda não existe.
    if 'verificacao_email' not in tabelas:
        VerificacaoEmail = apps.get_model('clientes', 'VerificacaoEmail')
        schema_editor.create_model(VerificacaoEmail)

    # Adiciona a coluna cliente_user_id em Cliente somente se ainda não existe.
    with connection.cursor() as cursor:
        colunas = [
            col.name
            for col in connection.introspection.get_table_description(cursor, 'cliente')
        ]
    if 'cliente_user_id' not in colunas:
        Cliente = apps.get_model('clientes', 'Cliente')
        schema_editor.add_field(Cliente, Cliente._meta.get_field('cliente_user'))


class Migration(migrations.Migration):
    dependencies = [
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            criar_tabelas_auth_se_necessario,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
