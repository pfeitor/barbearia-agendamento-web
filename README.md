# 💈 PI Barbearia

Sistema completo de agendamento online para barbearias, desenvolvido com Django.

---

## 📌 Sobre o Projeto

O **PI Barbearia** é uma aplicação web que permite o gerenciamento completo de agendamentos, profissionais, clientes e serviços em uma barbearia.

O sistema foi projetado para:

- 📅 Automatizar agendamentos
- 👤 Gerenciar clientes e profissionais
- ⏱️ Controlar disponibilidade de horários
- 📊 Organizar o fluxo de atendimento
- ✉️ Notificar clientes por e-mail automaticamente

---

## 🧠 Funcionalidades

### 👤 Cliente
- Cadastro com e-mail e senha
- Verificação de e-mail (código de 6 dígitos, expira em 15 min)
- Login por e-mail e senha
- Recuperação de senha por link seguro (expira em 1h)
- Criar agendamentos
- Visualizar agendamentos
- Cancelar agendamentos
- **Confirmar ou cancelar agendamento por link seguro no e-mail** (sem precisar fazer login)

### 🛠️ Administração
- Dashboard administrativo
- CRUD completo de:
  - Clientes
  - Profissionais
  - Serviços
  - Agendamentos
- Controle total do sistema

### ⏰ Sistema de Disponibilidade
- Cálculo automático de horários disponíveis
- Considera:
  - Escala do profissional
  - Horário de almoço
  - Duração do serviço
  - Agendamentos existentes

### ✉️ Sistema de Notificações por E-mail
- **Confirmação de agendamento** — enviada automaticamente ao cliente quando um novo agendamento é criado (status `AGENDADO`)
- **Lembrete com link de ação** — enviado nos dias D-3, D-1 e D-0 (configurável) para agendamentos pendentes; o cliente confirma ou cancela com um clique, sem precisar fazer login
- Canal configurável por ambiente: **Brevo API transacional** (`EMAIL_PROVIDER=brevo`) ou **SMTP** (`EMAIL_PROVIDER=smtp`)
- Todos os envios são registrados em `NotificacaoLog` (visível no painel admin)
- Lembrete diário executado por Cron Job no Render (zero custo adicional)

---

## 🏗️ Arquitetura

- **Framework**: Django 5+
- **Arquitetura**: Monolito (MVT)
- **Padrões utilizados**:
  - Class-Based Views (CBV)
  - Services Layer
  - Mixins de autenticação

---

## 🗄️ Banco de Dados

### Diagrama ER

![Diagrama ER](docs/mer-pi-barbearia.png)

> 🔗 [Visualizar diagrama interativo no dbdiagram.io](https://dbdiagram.io/d/mer-pi-barbearia-69c4953878c6c4bc7a6dd011)

### Principais tabelas

| Tabela | Descrição |
|--------|-----------|
| `cliente` | Clientes cadastrados na barbearia |
| `profissional` | Barbeiros/profissionais ativos |
| `servico` | Serviços oferecidos com duração e preço |
| `agendamento` | Agendamentos vinculando cliente, profissional e serviço |
| `professional_schedule` | Grade de horários semanais por profissional |
| `token_confirmacao_agendamento` | Tokens URL-safe para confirmação/cancelamento por link (expira no horário do agendamento) |
| `notificacao_log` | Histórico de todos os e-mails enviados pelo sistema |

---

## 📂 Estrutura do Projeto

```

├── config/             # Configurações do Django
├── apps/
│   ├── core/           # Autenticação e dashboards
│   ├── clientes/       # Gestão de clientes
│   ├── profissionais/  # Profissionais e escalas
│   ├── servicos/       # Catálogo de serviços
│   ├── agendamentos/   # Lógica principal de agendamento
│   └── notificacoes/   # Notificações por e-mail
│       ├── models.py           # NotificacaoLog
│       ├── services.py         # NotificacaoService
│       ├── providers.py        # Brevo API / SMTP
│       ├── admin.py            # Painel de logs
│       └── management/
│           └── commands/
│               └── enviar_lembretes.py  # Cron job de lembretes
├── templates/          # Templates HTML (inclui e-mails)
├── static/             # CSS e assets
├── requirements/       # Dependências por ambiente
├── manage.py
└── render.yaml         # Deploy (web + cron job)

````

---

## 🔐 Autenticação

O sistema possui dois tipos de acesso, ambos via e-mail e senha (`AUTH_USER_MODEL = 'clientes.ClienteUser'`):

- 👤 **Cliente** — `/clientes/login/`
  - Cadastro com verificação de e-mail (código 6 dígitos, expira 15 min)
  - Login por e-mail e senha
  - Recuperação de senha por link com token HMAC (expira 1h)
  - Acesso restrito às próprias páginas via `ClienteRequiredMixin`

- 🛠️ **Administrador** — `/clientes/login/` (is_staff=True)
  - Login por e-mail e senha
  - Acesso total ao sistema via `AdminRequiredMixin`
  - Autenticação via `AdminEmailBackend` (custom)

---

## ⚙️ Tecnologias

- Python 3.x
- Django
- PostgreSQL (produção)
- SQLite (desenvolvimento)
- Gunicorn
- WhiteNoise
- Render (deploy)

---

## 🚀 Como Rodar o Projeto

### 1. Clonar repositório

```bash
git clone <url-do-repositorio>
cd nome-do-projeto
````

---

### 2. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

---

### 3. Instalar dependências

```bash
pip install -r requirements/dev.txt
```

---

### 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

```env
# Django
SECRET_KEY=sua-chave-secreta
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=America/Sao_Paulo

# Notificações por E-mail
EMAIL_PROVIDER=brevo
DEFAULT_FROM_EMAIL=Minha Barbearia <noreply@seudominio.com>
BARBEARIA_NOME=Minha Barbearia

# Brevo API transacional (EMAIL_PROVIDER=brevo)
API_KEY_BREVO=xkeysib-placeholder
BREVO_SENDER_NAME=Minha Barbearia
BREVO_SENDER_EMAIL=noreply@seudominio.com
BREVO_TIMEOUT=10

# SMTP alternativo (EMAIL_PROVIDER=smtp)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
SMTP_EMAIL_HOST_USER=seuemail@gmail.com
SMTP_EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password do Google

# Links nos e-mails de lembrete
SITE_URL=http://127.0.0.1:8000
LEMBRETE_DIAS_ANTECEDENCIA=3,1,0

# Superusuário (criado automaticamente via bootstrap)
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=SenhaSegura123
```

> 💡 Em desenvolvimento, se `EMAIL_PROVIDER=brevo` estiver sem `API_KEY_BREVO` ou se o SMTP estiver sem senha, os e-mails são exibidos no terminal.

---

### 5. Aplicar migrações

```bash
python manage.py migrate
```

---

### 6. Criar superusuário

```bash
python manage.py createsuperuser
```

---

### 7. Rodar servidor

```bash
python manage.py runserver
```

---

### 8. Acessar sistema

* App: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* Login (clientes e admins): [http://127.0.0.1:8000/clientes/login/](http://127.0.0.1:8000/clientes/login/)
* Admin Django: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🔗 API de Disponibilidade

Endpoint:

```
GET /agendamentos/availability/
```

Parâmetros:

* `professional_id`
* `service_id`

Retorna:

* horários disponíveis com base nas regras do sistema

---

## ✉️ Notificações por E-mail

### Como funciona

| Momento | Gatilho | Descrição |
|---------|---------|----------|
| Criação | Agendamento salvo com status `AGENDADO` | E-mail com detalhes do agendamento enviado automaticamente via Django Signal |
| Lembrete D-3, D-1, D-0 | Cron Job diário às 11:00 UTC | E-mail com botões "Confirmar" e "Cancelar"; cliente age sem precisar de login. Intervalos configuráveis via `LEMBRETE_DIAS_ANTECEDENCIA` |

### Fluxo do link de confirmação

1. O cron gera (ou reutiliza) um token seguro por agendamento
2. O cliente recebe o e-mail e clica em **Confirmar** ou **Cancelar**
3. A view pública `/agendamentos/responder/<token>/` processa a ação e transiciona o status
4. Agendamentos já `CONFIRMADO` ou `CANCELADO` saem do filtro e não recebem novos lembretes

### Configurar Brevo API

1. Crie uma API key transacional na Brevo.
2. Valide o remetente/domínio na Brevo.
3. Configure `EMAIL_PROVIDER=brevo`, `API_KEY_BREVO`, `BREVO_SENDER_NAME`, `BREVO_SENDER_EMAIL` e `DEFAULT_FROM_EMAIL`.
4. Em produção, a aplicação falha na inicialização se `EMAIL_PROVIDER=brevo` estiver sem chave ou remetente.

### Configurar Gmail SMTP alternativo

1. Ative o **2FA** na sua conta Google: [myaccount.google.com/security](https://myaccount.google.com/security)
2. Gere uma **App Password** em: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Configure `EMAIL_PROVIDER=smtp`, `SMTP_EMAIL_HOST_USER` e `SMTP_EMAIL_HOST_PASSWORD` no `.env`

### Testar o lembrete manualmente

```bash
python manage.py enviar_lembretes
```

### Logs de notificação

Todos os envios (sucesso ou falha) são registrados na tabela `notificacao_log` e visíveis em:

```
http://127.0.0.1:8000/admin/notificacoes/notificacaolog/
```

### Deploy (Render)

O `render.yaml` já inclui um **Cron Job** configurado para rodar `python manage.py enviar_lembretes` diariamente às 08:00 BRT. No painel do Render, configure `EMAIL_PROVIDER=brevo`, `API_KEY_BREVO`, `BREVO_SENDER_NAME`, `BREVO_SENDER_EMAIL`, `DEFAULT_FROM_EMAIL` e `SITE_URL` para ativar os envios reais.

---

## 📈 Status do Projeto

✅ Funcional  
✅ Autenticação por e-mail/senha com verificação de e-mail e reset de senha  
✅ Sistema de notificações com lembrete ativo por link de confirmação  
🚀 Pronto para deploy em produção

---

## 📄 Licença

Este projeto é de uso acadêmico / educacional.

---

## 👨‍💻 Autor

Desenvolvido por **Paulo Feitor**
