# Documentação Técnica - PI Barbearia

## 1. Visão Geral

**Nome do projeto:** PI Barbearia  
**Objetivo:** sistema web para agendamento online em barbearias, com autenticação de clientes, painel administrativo, cálculo de disponibilidade e notificações transacionais por e-mail.  
**Arquitetura:** monolito Django seguindo o padrão MVT (Model-View-Template), organizado em apps por domínio.  
**Banco de dados:** PostgreSQL em produção, atualmente migrado para Neon, configurado por `DATABASE_URL`. SQLite continua disponível como fallback local quando `DATABASE_URL` não estiver definido.  
**Deploy:** Render, com Web Service e Cron Job para lembretes.

O sistema atende dois perfis principais:

- **Cliente:** registra conta, verifica e-mail, agenda serviços, acompanha seus agendamentos e pode confirmar/cancelar por link.
- **Administrador:** gerencia clientes, profissionais, horários, serviços e agendamentos pelo painel administrativo.

---

## 2. Arquitetura do Projeto

O projeto é um monolito Django com separação por apps:

| App | Responsabilidade |
|---|---|
| `core` | Dashboards, backend de autenticação admin por e-mail e mixins de acesso |
| `clientes` | Cliente, usuário de cliente, registro, verificação de e-mail, login e reset de senha |
| `profissionais` | Cadastro de profissionais e agenda semanal de disponibilidade |
| `servicos` | Catálogo de serviços, duração e preço |
| `agendamentos` | Criação, listagem, cancelamento, conclusão e confirmação por link |
| `notificacoes` | Providers de e-mail, serviço de envio e histórico de notificações |

Camadas principais:

- **Models:** entidades persistidas e relacionamentos.
- **Views:** orquestração de requests, permissões e renderização.
- **Forms:** validação de entrada.
- **Services:** regras de negócio e integrações internas.
- **Providers:** transporte externo de e-mail, isolado do restante da aplicação.
- **Templates:** HTML da aplicação e dos e-mails transacionais.

---

## 3. Estrutura de Diretórios

```text
.
├── apps/
│   ├── agendamentos/
│   ├── clientes/
│   ├── core/
│   ├── notificacoes/
│   ├── profissionais/
│   └── servicos/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/
│   ├── FEATURES/
│   └── DOCUMENTACAO_TECNICA.md
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── static/
├── templates/
├── manage.py
├── render.yaml
├── requirements.txt
└── .env.example
```

Arquivos importantes:

- `manage.py`: entry point Django, usando `config.settings.dev` por padrão.
- `config/settings/base.py`: configurações compartilhadas, banco, e-mail e segurança.
- `config/settings/dev.py`: ajustes locais, incluindo console backend para e-mails quando aplicável.
- `config/settings/prod.py`: HTTPS/cookies seguros para produção.
- `render.yaml`: definição do Web Service e Cron Job no Render.
- `.env.example`: referência das variáveis de ambiente.

---

## 4. Banco de Dados

### Configuração

O banco é definido por `DATABASE_URL`.

Regras atuais:

- Se `RENDER_BUILD_ID` existir, o build usa SQLite para evitar dependência do banco durante build.
- Se `DATABASE_URL` estiver definido, a aplicação usa essa URL, inclusive localmente.
- Se `DATABASE_URL` estiver vazio, a aplicação usa `db.sqlite3`.
- `DATABASE_SSL_REQUIRE=True` deve ser usado em produção/Neon.

Exemplos:

```env
# Local SQLite
DATABASE_URL=sqlite:///db.sqlite3
DATABASE_SSL_REQUIRE=False

# Local PostgreSQL
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DBNAME
DATABASE_SSL_REQUIRE=False

# Neon/produção
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
DATABASE_SSL_REQUIRE=True
```

### Migração Render para Neon

Os dados do PostgreSQL da Render foram migrados para a Neon por dump/restore.

Validações executadas na migração:

- conexão origem Render: OK;
- conexão destino Neon: OK;
- Neon vazia antes do restore;
- schema restaurado com 21 tabelas;
- contagens principais conferidas:
  - `agendamento=8`
  - `auth_permission=60`
  - `cliente=4`
  - `notificacao_log=4`
- `manage.py migrate --check` contra Neon: OK;
- `manage.py check` contra Neon: OK.

Após validar produção com Neon, qualquer dump local gerado deve ser removido por conter cópia completa do banco.

---

## 5. Models Principais

### `clientes.ClienteUser`

Usuário de autenticação customizado para clientes.

Campos relevantes:

- `email`: identificador único (`USERNAME_FIELD`).
- `is_active`: começa como `False` para clientes até verificação de e-mail.
- `is_staff` / `is_superuser`: usados para acesso administrativo.

### `clientes.Cliente`

Perfil de cliente usado nos agendamentos.

Campos:

- `nome`
- `telefone`
- `email`
- `cliente_user`: vínculo opcional `OneToOneField` com `ClienteUser`.
- `created_at`

### `clientes.VerificacaoEmail`

Controle de códigos de verificação de 6 dígitos.

Campos:

- `cliente_user`
- `code`
- `expires_at`
- `is_used`
- `created_at`

Regras:

- expiração em 15 minutos;
- limite de 3 tentativas por hora;
- códigos anteriores não usados são invalidados ao gerar novo código.

### `profissionais.Profissional`

Profissional que realiza atendimentos.

Campos:

- `nome`
- `ativo`
- `created_at`

### `profissionais.ProfessionalSchedule`

Agenda semanal de trabalho por profissional.

Campos:

- `profissional`
- `weekday`
- `start_time`
- `end_time`
- `lunch_start`
- `lunch_end`
- `is_day_off`
- `created_at`
- `updated_at`

Regras:

- combinação única de profissional e dia da semana;
- validação de horários de trabalho;
- validação de intervalo de almoço dentro do expediente.

### `servicos.Servico`

Serviço oferecido pela barbearia.

Campos:

- `nome`
- `duracao_minutos`
- `preco`

### `agendamentos.Agendamento`

Registro de agendamento.

Campos:

- `cliente`
- `profissional`
- `servico`
- `data_hora_inicio`
- `status`: `AGENDADO`, `CONFIRMADO`, `CANCELADO`, `CONCLUIDO`
- `confirmado_whatsapp`
- `created_at`

Índices:

- `data_hora_inicio`
- `status`
- `(profissional, data_hora_inicio)`

### `agendamentos.TokenConfirmacaoAgendamento`

Token público para confirmação/cancelamento de agendamento por link.

Campos:

- `agendamento`
- `token`
- `expires_at`
- `usado_em`
- `acao`

### `notificacoes.NotificacaoLog`

Histórico dos envios de e-mail ligados a agendamentos.

Campos:

- `agendamento`
- `tipo`: `CONFIRMACAO_SOLICITADA`, `LEMBRETE_DIA`, `LEMBRETE_COM_LINK`
- `destinatario`
- `status`: `ENVIADO` ou `FALHOU`
- `erro`
- `provider`: `smtp`, `brevo` ou `brevo-console`
- `provider_message_id`
- `enviado_em`

---

## 6. Autenticação e Segurança

### Modelo de autenticação

O projeto usa:

```python
AUTH_USER_MODEL = "clientes.ClienteUser"
```

Clientes e administradores autenticam por e-mail e senha.

Fluxos principais:

- registro de cliente;
- envio de código de verificação por e-mail;
- ativação da conta após validação do código;
- login por e-mail/senha;
- reset de senha com token HMAC do Django;
- admin com `is_staff=True`.

### Backends

```python
AUTHENTICATION_BACKENDS = [
    "apps.core.backends.AdminEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

O backend customizado permite autenticação administrativa por e-mail. O `ModelBackend` mantém compatibilidade com o fluxo padrão do Django.

### Controle de acesso

Mixins principais:

- `ClienteRequiredMixin`
- `AdminRequiredMixin`
- `AdminOrClienteMixin`

Regras:

- clientes acessam apenas seus próprios dados/agendamentos;
- administradores acessam CRUDs e painéis administrativos;
- links de confirmação/cancelamento por token são públicos, mas protegidos por token único, expiração e marcação de uso.

### Segurança operacional

- Secrets ficam em variáveis de ambiente.
- `.env` não deve ser commitado.
- `API_KEY_BREVO` é mascarada nos erros do provider.
- Em produção, `prod.py` habilita cookies seguros e `SECURE_PROXY_SSL_HEADER`.
- Em produção/Neon, usar `DATABASE_SSL_REQUIRE=True`.

---

## 7. Fluxos Principais

### Registro e verificação de e-mail

```text
POST /clientes/registrar/
→ ClienteRegisterView
→ cria ClienteUser(is_active=False) e Cliente
→ AuthService.gerar_e_enviar_codigo()
→ VerificacaoEmail(code, expires_at)
→ NotificacaoService.enviar_email_verificacao()
→ EmailProvider ativo
```

```text
POST /clientes/verificar/
→ AuthService.verificar_codigo()
→ marca código como usado
→ ativa ClienteUser
→ login automático
```

### Reset de senha

```text
POST /clientes/esqueci-senha/
→ AuthService.enviar_link_reset()
→ default_token_generator.make_token()
→ NotificacaoService.enviar_email_reset_senha()
→ e-mail com link absoluto
```

```text
POST /clientes/resetar-senha/<uidb64>/<token>/
→ AuthService.validar_token_reset()
→ ClienteUser.set_password()
→ is_active=True
```

### Criação de agendamento

```text
GET /agendamentos/novo/
→ AgendamentoCreateView
→ carrega profissionais, serviços e disponibilidade

POST /agendamentos/novo/
→ valida formulário e disponibilidade
→ cria Agendamento(status=AGENDADO)
→ post_save signal
→ NotificacaoService.enviar_confirmacao_agendamento()
→ NotificacaoLog
```

Falha de e-mail não desfaz a criação do agendamento. A falha é registrada em `NotificacaoLog`.

### Disponibilidade

Endpoint principal:

```text
GET /agendamentos/simple-final-availability/?professional_id=X&service_id=Y
```

Serviço:

```text
AvailabilityService.get_available_slots()
→ busca profissional ativo e serviço
→ calcula intervalo de datas
→ carrega escala semanal
→ remove horários ocupados por AGENDADO/CONFIRMADO
→ remove almoço
→ gera slots de 30 minutos compatíveis com a duração do serviço
→ cacheia por 5 minutos
```

### Confirmação/cancelamento por link

```text
python manage.py enviar_lembretes
→ busca agendamentos AGENDADO em D-3, D-1 e D-0
→ ConfirmacaoLinkService.obter_ou_criar_token()
→ NotificacaoService.enviar_lembrete_com_link()
→ cliente acessa /agendamentos/responder/<token>/
→ ConfirmacaoLinkService.processar()
→ status vira CONFIRMADO ou CANCELADO
→ token marcado como usado
```

---

## 8. Notificações por E-mail

### Provider configurável

O transporte é escolhido por:

```env
EMAIL_PROVIDER=smtp
# ou
EMAIL_PROVIDER=brevo
```

Implementação:

- `apps/notificacoes/providers.py`
- `EmailProvider`
- `DjangoEmailProvider`
- `BrevoEmailProvider`
- `EmailSendResult`

### Brevo

Provider recomendado em produção:

```env
EMAIL_PROVIDER=brevo
API_KEY_BREVO=xkeysib-...
BREVO_SENDER_NAME=Minha Barbearia
BREVO_SENDER_EMAIL=noreply@seudominio.com
BREVO_TIMEOUT=10
DEFAULT_FROM_EMAIL=Minha Barbearia <noreply@seudominio.com>
```

Regras:

- usa `sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email`;
- não usa campanhas, listas ou contatos de marketing;
- exige `API_KEY_BREVO`, `BREVO_SENDER_NAME` e `BREVO_SENDER_EMAIL` em produção;
- em desenvolvimento, se `EMAIL_PROVIDER=brevo` estiver sem `API_KEY_BREVO`, usa console backend (`brevo-console`);
- erros são sanitizados para não vazar a API key.

### SMTP

Provider alternativo:

```env
EMAIL_PROVIDER=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
SMTP_EMAIL_HOST_USER=seuemail@gmail.com
SMTP_EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=Minha Barbearia <seuemail@gmail.com>
```

### Fluxos atendidos

- confirmação de agendamento;
- lembrete do dia;
- lembrete com link de confirmação/cancelamento;
- verificação de e-mail;
- reset de senha.

### Observabilidade

Para notificações ligadas a agendamento, o sistema registra:

- tipo;
- destinatário;
- status;
- erro, quando houver;
- provider;
- message id retornado pelo provider, quando disponível.

Admin:

```text
/admin/notificacoes/notificacaolog/
```

---

## 9. Settings e Variáveis de Ambiente

### Variáveis obrigatórias ou relevantes

| Variável | Uso |
|---|---|
| `SECRET_KEY` | Chave secreta Django |
| `DEBUG` | Booleano (`True` ou `False`) |
| `ALLOWED_HOSTS` | Hosts permitidos |
| `DATABASE_URL` | URL do banco principal |
| `DATABASE_SSL_REQUIRE` | SSL obrigatório no banco |
| `TIME_ZONE` | Fuso, padrão `America/Sao_Paulo` |
| `EMAIL_PROVIDER` | `smtp` ou `brevo` |
| `DEFAULT_FROM_EMAIL` | Remetente padrão |
| `BARBEARIA_NOME` | Nome exibido nos e-mails |
| `API_KEY_BREVO` | Chave Brevo |
| `BREVO_SENDER_NAME` | Nome do remetente Brevo |
| `BREVO_SENDER_EMAIL` | E-mail remetente validado na Brevo |
| `BREVO_TIMEOUT` | Timeout HTTP Brevo |
| `SMTP_EMAIL_HOST_USER` | Usuário SMTP |
| `SMTP_EMAIL_HOST_PASSWORD` | Senha SMTP |
| `SITE_URL` | URL base para links gerados fora de request |
| `LEMBRETE_DIAS_ANTECEDENCIA` | Intervalos de lembrete, ex. `3,1,0` |
| `DJANGO_SUPERUSER_EMAIL` | Superusuário do bootstrap |
| `DJANGO_SUPERUSER_PASSWORD` | Senha do superusuário do bootstrap |

### Atenção

`DEBUG` precisa ser booleano aceito pelo `python-decouple`, como:

```env
DEBUG=True
DEBUG=False
```

Valores como `release` não são válidos.

---

## 10. Deploy no Render

### Web Service

Executa a aplicação Django via Gunicorn.

Comandos atuais:

```text
buildCommand: pip install -r requirements/prod.txt && python manage.py collectstatic --noinput
preDeployCommand: python manage.py bootstrap
startCommand: python manage.py bootstrap && gunicorn config.wsgi:application
```

Variáveis esperadas no Web Service:

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

Executa:

```text
python manage.py enviar_lembretes
```

Horário configurado:

```text
0 11 * * *
```

Equivale a 08:00 BRT.

O Cron Job precisa das mesmas variáveis de banco, e-mail e `SITE_URL` usadas pelo Web Service.

---

## 11. Dependências

Principais dependências:

| Dependência | Uso |
|---|---|
| `Django>=5.1,<6.1` | Framework web |
| `gunicorn` | Servidor WSGI em produção |
| `whitenoise` | Arquivos estáticos |
| `dj-database-url` | Parse de `DATABASE_URL` |
| `psycopg[binary]` | Driver PostgreSQL |
| `python-decouple` | Variáveis de ambiente |
| `sib-api-v3-sdk` | API transacional Brevo |

Instalação:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 12. Testes e Validação

Comandos úteis:

```powershell
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py check
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py test apps.notificacoes.tests
```

Validações já realizadas:

- `manage.py check`: OK;
- testes de `apps.notificacoes.tests`: OK;
- `makemigrations --check --dry-run`: sem mudanças pendentes;
- import de `sib_api_v3_sdk`: OK após instalar requirements;
- smoke local de reset de senha via Brevo: OK;
- envio real na Render via Brevo: OK após configurar `EMAIL_PROVIDER=brevo`;
- migração Render → Neon: OK.

Limitações conhecidas:

- `python manage.py test` sem label pode não descobrir testes em alguns cenários; usar labels explícitos quando necessário.
- Ainda é desejável adicionar testes específicos para o management command `enviar_lembretes`.

---

## 13. Como Rodar Localmente

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

Base local com SQLite:

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

Com `EMAIL_PROVIDER=brevo` e `API_KEY_BREVO` vazia em desenvolvimento, e-mails são impressos no terminal.

### 4. Migrar banco

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

### 5. Criar superusuário

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Ou usar o comando de bootstrap, se as variáveis `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` estiverem definidas:

```powershell
.\.venv\Scripts\python.exe manage.py bootstrap
```

### 6. Subir servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

URLs principais:

- aplicação: `http://127.0.0.1:8000/`
- login cliente: `http://127.0.0.1:8000/clientes/login/`
- admin Django: `http://127.0.0.1:8000/admin/`
- novo agendamento: `http://127.0.0.1:8000/agendamentos/novo/`

---

## 14. Frontend e Templates

O frontend é server-side rendered com templates Django.

Templates principais:

- `templates/base.html`
- `templates/core/`
- `templates/clientes/`
- `templates/agendamentos/`
- `templates/notificacoes/`
- `apps/notificacoes/templates/notificacoes/`

Características:

- navegação condicional por perfil;
- mensagens via Django messages framework;
- CSRF em formulários;
- CSS centralizado em `static/css/styles.css`;
- e-mails HTML renderizados com templates Django.

---

## 15. Pontos de Atenção

### Segurança de secrets

- Nunca commitar `.env`.
- Não expor connection strings em issues, commits ou documentação.
- Se uma connection string aparecer em chat/log público, rotacionar senha/role no provedor.
- Remover dumps locais de banco após uso.

### E-mail em produção

- `EMAIL_PROVIDER=brevo` deve estar configurado no Web Service e no Cron Job.
- `BREVO_SENDER_EMAIL` precisa estar validado na Brevo.
- Se o log mostrar `via smtp` em produção, o provider não foi configurado corretamente.

### Banco

- Depois da migração para Neon, `DATABASE_URL` do Render deve apontar para Neon.
- Usar `DATABASE_SSL_REQUIRE=True` em produção.
- Rodar `manage.py migrate --check` após troca de banco.

### Testes

- A cobertura ainda pode crescer em:
  - `enviar_lembretes`;
  - reset de senha com provider mockado;
  - verificação de e-mail com provider mockado;
  - settings de e-mail e banco.

### Documentação externa

O diagrama do banco para dbdiagram.io foi gerado em formato DBML a partir da Neon, com 21 tabelas e 21 referências.

---

## 16. Status Atual

O sistema está funcional com:

- autenticação por e-mail/senha;
- verificação de e-mail por código;
- reset de senha por link;
- CRUD administrativo;
- cálculo de disponibilidade;
- confirmação/cancelamento por link;
- envio transacional por Brevo;
- logs de notificação;
- PostgreSQL migrado para Neon;
- deploy na Render.

Pendências recomendadas:

- atualizar variáveis do Cron Job no Render para Brevo/Neon, se ainda não estiverem iguais ao Web Service;
- executar smoke do `enviar_lembretes` em produção;
- remover dumps locais de banco após validação final;
- ampliar testes automatizados dos fluxos de notificação.

---

## 17. Histórico Recente

- Implementada troca de SMTP para provider configurável SMTP/Brevo.
- Validado envio real via Brevo na Render.
- Migrado PostgreSQL da Render para Neon.
- Gerado DBML atualizado para dbdiagram.io.
- Atualizada documentação técnica para refletir o estado atual do projeto.
