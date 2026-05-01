"""
Adiciona o sistema de autenticação por e-mail ao app clientes:
  - ClienteUser (AUTH_USER_MODEL)
  - VerificacaoEmail
  - Cliente.cliente_user (OneToOneField → ClienteUser, nullable)

Compatível com bancos existentes que possuem apenas a tabela 'cliente'
criada pelo 0001_initial.
"""

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('clientes', '0001_initial'),
    ]

    operations = [
        # ── 1. ClienteUser ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='ClienteUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(
                    default=False,
                    help_text='Designates that this user has all permissions without explicitly assigning them.',
                    verbose_name='superuser status',
                )),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='e-mail')),
                ('is_active', models.BooleanField(default=False, verbose_name='ativo')),
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'verbose_name': 'usuário cliente',
                'verbose_name_plural': 'usuários clientes',
                'db_table': 'cliente_user',
            },
        ),

        # ── 2. VerificacaoEmail ───────────────────────────────────────────────
        migrations.CreateModel(
            name='VerificacaoEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('cliente_user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='verificacoes',
                    to='clientes.clienteuser',
                )),
            ],
            options={'db_table': 'verificacao_email', 'ordering': ['-created_at']},
        ),

        # ── 3. FK Cliente → ClienteUser ───────────────────────────────────────
        migrations.AddField(
            model_name='cliente',
            name='cliente_user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='perfil',
                to='clientes.clienteuser',
            ),
        ),
    ]
