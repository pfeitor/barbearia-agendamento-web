# PI Barbearia

Sistema web de agendamento online para barbearias, desenvolvido com Django.

## Sobre

O **PI Barbearia** permite gerenciar clientes, profissionais, serviços, horários de atendimento e agendamentos. O sistema possui autenticação por e-mail/senha, cálculo automático de disponibilidade, confirmação/cancelamento por link e envio de e-mails transacionais.

Perfis atendidos:

- **Cliente:** cria conta, verifica e-mail, agenda serviços, acompanha seus agendamentos e pode confirmar/cancelar por link.
- **Administrador:** gerencia clientes, profissionais, serviços, escalas e agendamentos.

## Funcionalidades

### Cliente

- Cadastro com e-mail e senha.
- Verificação de e-mail por código de 6 dígitos.
- Login por e-mail e senha.
- Recuperação de senha por link seguro.
- Criação e visualização de agendamentos.
- Cancelamento de agendamentos.
- Confirmação ou cancelamento por link recebido por e-mail, sem necessidade de login.

### Administração

- Dashboard administrativo.
- CRUD de clientes.
- CRUD de profissionais.
- CRUD de serviços.
- CRUD e acompanhamento de agendamentos.
- Conclusão de agendamentos.
- Visualização dos logs de notificação.

### Disponibilidade

O cálculo de horários disponíveis considera:

- escala semanal do profissional;
- dias de folga;
- horário de almoço;
- duração do serviço;
- agendamentos existentes com status `AGENDADO` ou `CONFIRMADO`.

### Notificações por E-mail

- Confirmação automática de agendamento.
- Verificação de e-mail no cadastro.
- Reset de senha.
- Lembretes D-3, D-1 e D-0 com link para confirmar ou cancelar.
- Provider configurável: Brevo API transacional ou SMTP.
- Histórico em `NotificacaoLog`.

## Stack

- Python
- Django
- PostgreSQL
- Neon PostgreSQL
- Render
- Gunicorn
- WhiteNoise
- Brevo API transacional
- SQLite como fallback local

## Arquitetura

O projeto é um monolito Django no padrão MVT, organizado por apps:

| App | Responsabilidade |
|---|---|
| `core` | Dashboards, backend admin por e-mail e mixins de acesso |
| `clientes` | Clientes, autenticação, verificação de e-mail e reset de senha |
| `profissionais` | Profissionais e agenda semanal |
| `servicos` | Catálogo de serviços |
| `agendamentos` | Criação, listagem, cancelamento, conclusão e confirmação por link |
| `notificacoes` | Providers de e-mail, serviço de envio e logs |

Estrutura resumida:

```text
.
├── apps/
│   ├── agendamentos/
│   ├── clientes/
│   ├── core/
│   ├── notificacoes/
│   │   ├── models.py
│   │   ├── providers.py
│   │   ├── services.py
│   │   └── management/commands/enviar_lembretes.py
│   ├── profissionais/
│   └── servicos/
├── config/
│   └── settings/
├── docs/
├── requirements/
├── static/
├── templates/
├── manage.py
└── render.yaml
```

## Banco de Dados

O banco principal é definido por `DATABASE_URL`.

Regras atuais:

- Se `DATABASE_URL` estiver definido, a aplicação usa essa URL, inclusive localmente.
- Se `DATABASE_URL` estiver vazio, usa SQLite local (`db.sqlite3`).
- Durante build no Render, o projeto usa SQLite para evitar dependência do banco.
- Em produção/Neon, use `DATABASE_SSL_REQUIRE=True`.

Exemplos:

```env
# SQLite local
DATABASE_URL=sqlite:///db.sqlite3
DATABASE_SSL_REQUIRE=False

# PostgreSQL local
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DBNAME
DATABASE_SSL_REQUIRE=False

# Neon/produção
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
DATABASE_SSL_REQUIRE=True
```

### Diagrama ER

![Diagrama ER](docs/mer-pi-barbearia.png)

Diagrama interativo:

https://dbdiagram.io/d/mer-pi-barbearia-69c4953878c6c4bc7a6dd011

Principais tabelas:

| Tabela | Descrição |
|---|---|
| `cliente_user` | Usuários de autenticação dos clientes/admins |
| `cliente` | Perfis de clientes |
| `verificacao_email` | Códigos de verificação de e-mail |
| `profissional` | Profissionais |
| `professional_schedule` | Grade semanal de disponibilidade |
| `servico` | Serviços |
| `agendamento` | Agendamentos |
| `token_confirmacao_agendamento` | Tokens de confirmação/cancelamento por link |
| `notificacao_log` | Histórico de envios de e-mail |

## Autenticação

O projeto usa:

```python
AUTH_USER_MODEL = "clientes.ClienteUser"
```

Fluxos:

- Cliente registra e-mail/senha.
- Sistema envia código de verificação.
- Conta é ativada após validação do código.
- Login é feito por e-mail e senha.
- Reset de senha usa token padrão do Django, com expiração configurada por `PASSWORD_RESET_TIMEOUT`.
- Administradores são `ClienteUser` com `is_staff=True`.

URLs principais:

- Login: `/clientes/login/`
- Registro: `/clientes/registrar/`
- Verificação: `/clientes/verificar/`
- Esqueci minha senha: `/clientes/esqueci-senha/`
- Admin Django: `/admin/`

## Notificações

O envio fica centralizado em `apps/notificacoes/services.py` e o transporte em `apps/notificacoes/providers.py`.

Providers:

- `EMAIL_PROVIDER=brevo`: usa API transacional da Brevo.
- `EMAIL_PROVIDER=smtp`: usa backend SMTP do Django.
- Em desenvolvimento, `EMAIL_PROVIDER=brevo` sem `API_KEY_BREVO` usa console backend (`brevo-console`).

Configuração Brevo:

```env
EMAIL_PROVIDER=brevo
API_KEY_BREVO=xkeysib-...
BREVO_SENDER_NAME=Minha Barbearia
BREVO_SENDER_EMAIL=noreply@seudominio.com
BREVO_TIMEOUT=10
DEFAULT_FROM_EMAIL=Minha Barbearia <noreply@seudominio.com>
```

Configuração SMTP alternativa:

```env
EMAIL_PROVIDER=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
SMTP_EMAIL_HOST_USER=seuemail@gmail.com
SMTP_EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=Minha Barbearia <seuemail@gmail.com>
```

Logs:

```text
/admin/notificacoes/notificacaolog/
```

Campos registrados:

- tipo;
- destinatário;
- status;
- erro;
- provider;
- provider message id;
- data/hora.

## Lembretes e Confirmação por Link

O comando abaixo envia lembretes para agendamentos `AGENDADO` conforme `LEMBRETE_DIAS_ANTECEDENCIA`:

```powershell
.\.venv\Scripts\python.exe manage.py enviar_lembretes
```

Fluxo:

1. O comando busca agendamentos em D-3, D-1 e D-0, ou conforme configuração.
2. O sistema cria ou reutiliza `TokenConfirmacaoAgendamento`.
3. O cliente recebe links de confirmação e cancelamento.
4. A URL pública `/agendamentos/responder/<token>/` processa a ação.
5. O status muda para `CONFIRMADO` ou `CANCELADO`.

Variáveis:

```env
SITE_URL=https://barbearia-agendamento-web.onrender.com
LEMBRETE_DIAS_ANTECEDENCIA=3,1,0
```

## Como Rodar Localmente

### 1. Criar ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar `.env`

Copie o exemplo:

```powershell
Copy-Item .env.example .env
```

Exemplo mínimo local:

```env
SECRET_KEY=dev-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
DATABASE_SSL_REQUIRE=False
TIME_ZONE=America/Sao_Paulo

EMAIL_PROVIDER=brevo
API_KEY_BREVO=
DEFAULT_FROM_EMAIL=Minha Barbearia <noreply@localhost>
BARBEARIA_NOME=Minha Barbearia

SITE_URL=http://127.0.0.1:8000
LEMBRETE_DIAS_ANTECEDENCIA=3,1,0
```

`DEBUG` deve ser booleano (`True` ou `False`). Valores como `release` não são válidos para `python-decouple`.

### 4. Aplicar migrations

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

### 5. Criar superusuário

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Ou, com `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` configurados:

```powershell
.\.venv\Scripts\python.exe manage.py bootstrap
```

### 6. Rodar servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Acessos:

- App: http://127.0.0.1:8000/
- Login: http://127.0.0.1:8000/clientes/login/
- Admin: http://127.0.0.1:8000/admin/
- Novo agendamento: http://127.0.0.1:8000/agendamentos/novo/

## Testes e Validação

Comandos úteis:

```powershell
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py check
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py test apps.notificacoes.tests
```

Validações recentes:

- envio real via Brevo na Render;
- migração PostgreSQL Render para Neon;
- `manage.py migrate --check` contra Neon;
- `manage.py check` contra Neon;
- DBML atualizado para dbdiagram.io.

## Deploy

O deploy é feito no Render.

### Web Service

Variáveis principais:

```env
DATABASE_URL=<connection string Neon>
DATABASE_SSL_REQUIRE=True
SECRET_KEY=<secret>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
EMAIL_PROVIDER=brevo
API_KEY_BREVO=<secret>
BREVO_SENDER_NAME=Minha Barbearia
BREVO_SENDER_EMAIL=<remetente-validado>
DEFAULT_FROM_EMAIL=Minha Barbearia <remetente-validado>
BARBEARIA_NOME=Minha Barbearia
SITE_URL=https://barbearia-agendamento-web.onrender.com
DJANGO_SUPERUSER_EMAIL=<email>
DJANGO_SUPERUSER_PASSWORD=<senha>
```

### Cron Job

O `render.yaml` possui um Cron Job para:

```text
python manage.py enviar_lembretes
```

Agenda:

```text
0 11 * * *
```

Equivale a 08:00 BRT.

O Cron Job precisa das mesmas variáveis de banco, Brevo e `SITE_URL` usadas pelo Web Service.

## Segurança Operacional

- Não commitar `.env`.
- Não expor `DATABASE_URL`, `API_KEY_BREVO` ou senhas.
- Se uma credencial aparecer em chat/log/documento, rotacionar a senha no provedor.
- Remover dumps locais de banco após migrações.
- Usar `DATABASE_SSL_REQUIRE=True` em produção.
- Usar remetente validado na Brevo.

## Documentação

- Documentação técnica: [docs/DOCUMENTACAO_TECNICA.md](docs/DOCUMENTACAO_TECNICA.md)
- Arquitetura: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Features: [docs/FEATURES](docs/FEATURES)

## Status

Funcional:

- autenticação por e-mail/senha;
- verificação de e-mail;
- reset de senha;
- agendamentos;
- cálculo de disponibilidade;
- confirmação/cancelamento por link;
- notificações via Brevo;
- PostgreSQL na Neon;
- deploy na Render.

Pendências recomendadas:

- validar `enviar_lembretes` em produção após confirmar variáveis do Cron Job;
- ampliar testes automatizados para comando de lembretes, reset e verificação;
- remover dumps locais antigos após validação final.

## Licença

Projeto acadêmico/educacional.

## Autor

Desenvolvido por **Paulo Feitor**.
