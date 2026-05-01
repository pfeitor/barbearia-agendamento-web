# ARCHITECTURE.md — Barbearia Agendamento Web

## 1. Visão Geral

Sistema de agendamento online para barbearia, com dois perfis de usuário (cliente e administrador), cálculo dinâmico de slots disponíveis e notificações por e-mail.

| Item | Valor |
|---|---|
| Framework | Django 5.1+ |
| Linguagem | Python 3.x |
| DB Desenvolvimento | SQLite (`db.sqlite3`) |
| DB Produção | PostgreSQL (via `dj_database_url`) |
| Servidor WSGI | Gunicorn |
| Arquivos Estáticos | WhiteNoise |
| Deploy | Render.com (`render.yaml`) |
| Localização | pt-BR / `America/Sao_Paulo` |
| Package Manager | pip (`requirements/`) |

---

## 2. Estrutura de Diretórios

```
barbearia-agendamento-web/
├── apps/
│   ├── core/           # Autenticação, dashboards, mixins de permissão
│   ├── clientes/       # CRUD de clientes
│   ├── profissionais/  # CRUD de profissionais + grade de horários
│   ├── servicos/       # CRUD de serviços (nome, duração, preço)
│   ├── agendamentos/   # Lógica principal: slots, reservas, cancelamento
│   └── notificacoes/   # Envio de e-mails e log de notificações
├── config/
│   ├── settings/
│   │   ├── base.py     # Configurações compartilhadas
│   │   ├── dev.py      # DEBUG=True, e-mail no console
│   │   └── prod.py     # HTTPS, cookies seguros
│   ├── urls.py         # Roteador raiz
│   └── wsgi.py
├── templates/          # Templates Django por app
├── static/css/         # Estilos globais
├── requirements/
│   ├── base.txt        # Dependências comuns
│   ├── dev.txt
│   └── prod.txt
├── render.yaml         # Serviços web + cron no Render.com
├── manage.py
└── .env.example        # Variáveis de ambiente documentadas
```

---

## 3. Pontos de Entrada & Fluxo

### Inicialização
`manage.py` → `config.wsgi:application` (produção via Gunicorn)

### Roteamento Raiz (`config/urls.py`)

| Prefixo | App |
|---|---|
| _(raiz)_ | `apps.core` |
| `clientes/` | `apps.clientes` (inclui `/login/`, `/registrar/`, `/verificar/`, `/esqueci-senha/`, `/resetar-senha/`) |
| `profissionais/` | `apps.profissionais` |
| `servicos/` | `apps.servicos` |
| `agendamentos/` | `apps.agendamentos` (inclui `/<pk>/concluir/`) |
| `admin/` | Django Admin |

### Fluxo Principal de Agendamento
```
Cliente (e-mail/senha) → ClienteLoginView → Django auth session (ClienteUser)
→ AgendamentoCreateView → availability_api_view (JSON)
→ AvailabilityService.get_slots() → cache (5 min)
→ Agendamento.save() → post_save signal → enviar e-mail de confirmação
```

### Fluxo de Conclusão de Agendamento (Admin)
```
Admin → POST /agendamentos/<pk>/concluir/ → AgendamentoConcluirView (AdminRequiredMixin)
→ Agendamento.status = CONCLUIDO → post_save signal → invalida cache de disponibilidade
```

### Fluxo de Lembrete (Cron)
```
Render cron (11:00 UTC diário) → manage.py enviar_lembretes
→ NotificacaoService.enviar_lembrete_dia() → Gmail SMTP → NotificacaoLog
```

---

## 4. Padrões de Arquitetura

**Estilo:** MVT (Model-View-Template) Django padrão, com camada de serviço explícita em `agendamentos/services.py` e `notificacoes/services.py`.

### Responsabilidades por Camada

| Camada | Localização | Responsabilidade |
|---|---|---|
| Model | `*/models.py` | Entidades, validações, constraints de DB |
| View | `*/views.py` | Orquestração de request/response, autenticação |
| Service | `agendamentos/services.py` | Lógica de slots e disponibilidade |
| Service | `clientes/services.py` | `AuthService`: verificação de e-mail e reset de senha |
| Service | `notificacoes/services.py` | Envio de e-mails (confirmação, lembrete, verificação, reset) |
| Form | `*/forms.py` | Validação de entrada do usuário |
| Signal | `agendamentos/signals.py` | Efeitos colaterais desacoplados (cache, notificações) |
| Mixin | `core/mixins.py` | Controle de acesso reutilizável por CBV |

### Novos Models (feature-01)

| Model | App | Descrição |
|---|---|---|
| `ClienteUser` | `clientes` | AUTH_USER_MODEL; email como USERNAME_FIELD; is_active=False por padrão |
| `VerificacaoEmail` | `clientes` | Código 6 dígitos, expira 15min, limite 3/hora |
| `Cliente.cliente_user` | `clientes` | OneToOneField → ClienteUser (null=True para migração) |

### Autenticação por E-mail/Senha

| Perfil | Mecanismo | Backend |
|---|---|---|
| Cliente | Django auth via `ClienteUser` (email + senha) | `ModelBackend` |
| Admin | Django auth via `ClienteUser` (is_staff=True) | `AdminEmailBackend` (custom) |

`AUTH_USER_MODEL = 'clientes.ClienteUser'`. Clientes possuem `ClienteUser` (auth) vinculado ao perfil `Cliente` (dados) via `OneToOneField(related_name='perfil')`. Acesso protegido pelos mixins `ClienteRequiredMixin` (verifica `request.user.perfil`) e `AdminRequiredMixin` (verifica `is_staff`).

### Fluxo de Registro e Verificação de E-mail

```
POST /clientes/registrar/ → ClienteRegisterView
  → ClienteUser(is_active=False) + Cliente criados
  → AuthService.gerar_e_enviar_codigo() → VerificacaoEmail (expira 15min, limite 3/hora)
  → NotificacaoService.enviar_email_verificacao() → Gmail SMTP

POST /clientes/verificar/ → VerificarEmailView
  → AuthService.verificar_codigo() → ClienteUser.is_active=True → login automático
```

### Fluxo de Reset de Senha

```
POST /clientes/esqueci-senha/ → EsqueciSenhaView
  → AuthService.enviar_link_reset(cliente_user, request)
  → default_token_generator.make_token() (HMAC+timestamp, expira 1h via PASSWORD_RESET_TIMEOUT)
  → NotificacaoService.enviar_email_reset_senha() → request.build_absolute_uri() → Gmail SMTP

POST /clientes/resetar-senha/<uidb64>/<token>/ → ResetarSenhaView
  → AuthService.validar_token_reset() → ClienteUser.set_password() → is_active=True
```

> `request.build_absolute_uri()` garante que o link no e-mail inclui o domínio correto em todos os ambientes (`http://127.0.0.1:8000` local, `https://barbearia-agendamento-web.onrender.com` em produção).

### Validações de Senha

- Mínimo 8 caracteres (`MinimumLengthValidator`)
- Ao menos 1 letra maiúscula e 1 dígito (validação customizada nos formulários)
- Não pode ser puramente numérica (`NumericPasswordValidator`)
- Configurado em `AUTH_PASSWORD_VALIDATORS` em `config/settings/base.py`

### Conclusão de Agendamento (Admin)

`AgendamentoConcluirView` (POST-only, `AdminRequiredMixin`) transiciona `AGENDADO` ou `CONFIRMADO` → `CONCLUIDO`. O `post_save` signal existente invalida o cache de disponibilidade automaticamente.

### Disponibilidade com Cache

`AvailabilityService` calcula slots livres considerando: horário de trabalho semanal (`ProfessionalSchedule`), intervalo de almoço, duração do serviço e agendamentos existentes. Resultado cacheado por 5 minutos; invalidado via signals em criação/edição/exclusão de agendamentos.

---

## 5. Configurações & Infra

### Variáveis de Ambiente Essenciais

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta Django |
| `DEBUG` | `True` (dev) / `False` (prod) |
| `DATABASE_URL` | URL PostgreSQL (prod) ou SQLite (dev) |
| `ALLOWED_HOSTS` | Ex: `.onrender.com,localhost` |
| `TIME_ZONE` | Default: `America/Sao_Paulo` |
| `EMAIL_HOST_USER` | Conta Gmail para envio |
| `EMAIL_HOST_PASSWORD` | App Password Gmail |
| `DEFAULT_FROM_EMAIL` | Endereço remetente |
| `BARBEARIA_NOME` | Nome exibido nos e-mails |
| `DJANGO_SUPERUSER_*` | Criação automática de superuser via `bootstrap` |
| `PASSWORD_RESET_TIMEOUT` | TTL do token de reset de senha em segundos (padrão: `3600`) |

### Deploy (Render.com — `render.yaml`)

| Serviço | Tipo | Comando |
|---|---|---|
| `pi-barbearia` | Web (free) | `gunicorn config.wsgi:application` |
| `lembrete-agendamentos` | Cron (`0 11 * * *`) | `manage.py enviar_lembretes` |

- Build: `pip install -r requirements/prod.txt && python manage.py collectstatic --noinput`
- Pre-deploy: `python manage.py migrate`
- Banco: PostgreSQL gerenciado pelo Render, injetado via `DATABASE_URL`

### Seleção de Banco por Ambiente

```python
if os.getenv("RENDER_SERVICE_TYPE") == "web" and not os.getenv("RENDER_BUILD_ID"):
    DATABASES = {"default": dj_database_url.config(...)}  # PostgreSQL
else:
    DATABASES = {"default": {"ENGINE": "sqlite3", ...}}   # SQLite
```

---

## 6. Dependências Críticas

| Pacote | Função |
|---|---|
| `Django>=5.1` | Framework principal |
| `gunicorn` | Servidor WSGI de produção |
| `whitenoise` | Servir arquivos estáticos sem nginx |
| `dj-database-url` | Parse de `DATABASE_URL` |
| `psycopg[binary]` | Driver PostgreSQL |
| `python-decouple` | Leitura de variáveis de ambiente / `.env` |

---

## 7. Testes & Qualidade

- **Framework:** `unittest` Django (`TestCase`) em `*/tests.py`
- **Apps com testes:** `clientes`, `profissionais`, `servicos`, `agendamentos`, `notificacoes`
- **Lint/Format:** [NÃO DETECTADO] — sem configuração de flake8, black ou ruff
- **Pre-commit hooks:** [NÃO DETECTADO]
- **CI/CD:** [NÃO DETECTADO] — sem `.github/workflows/`
- **Execução:** `python manage.py test`

---

## 8. Limitações & Débitos Técnicos

### Outros Débitos

| Item | Descrição |
|---|---|
| Sem CI/CD | Testes não são executados automaticamente no push |
| Sem lint configurado | Qualidade de código não é verificada por tooling |
| `secret_key.txt` no repositório | Arquivo gerado localmente; verificar `.gitignore` |
| Cache em memória local | `django.core.cache.backends.locmem` — não compartilhado entre workers/instâncias |
| Sem task queue | Notificações síncronas no request cycle; lembretes via cron externo |
| `Cliente.cliente_user` nullable | OneToOneField com null=True; clientes criados pelo admin via painel CRUD não possuem `ClienteUser`. Clientes pré-existentes recebem `ClienteUser` via migração `0002` (senha inutilizável, devem resetar). |

---

## Como Usar em Futuras Sessões

> Antes de responder ou modificar código, leia este arquivo. Ele contém o mapa completo da arquitetura, fluxo e configurações. Não varra o repositório inteiro a menos que seja estritamente necessário para a tarefa. Se precisar de detalhes de um módulo, consulte apenas os caminhos listados na seção "Estrutura de Diretórios" ou "Pontos de Entrada".
