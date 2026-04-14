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

---

## 🧠 Funcionalidades

### 👤 Cliente
- Login simplificado por telefone
- Criar agendamentos
- Visualizar agendamentos
- Atualizar dados pessoais

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

---

## 🏗️ Arquitetura

- **Framework**: Django 5+
- **Arquitetura**: Monolito (MVT)
- **Padrões utilizados**:
  - Class-Based Views (CBV)
  - Services Layer
  - Mixins de autenticação

---

## 📂 Estrutura do Projeto

```

├── config/             # Configurações do Django
├── apps/
│   ├── core/           # Autenticação e dashboards
│   ├── clientes/       # Gestão de clientes
│   ├── profissionais/  # Profissionais e escalas
│   ├── servicos/       # Catálogo de serviços
│   ├── agendamentos/   # Lógica principal
│   └── notificacoes/   # (em desenvolvimento)
├── templates/          # Templates HTML
├── static/             # CSS e assets
├── requirements/       # Dependências por ambiente
├── manage.py
└── render.yaml         # Deploy

````

---

## 🔐 Autenticação

O sistema possui dois tipos de acesso:

- 👤 **Cliente**
  - Login via telefone (sem senha)
  - Sessão personalizada

- 🛠️ **Administrador**
  - Login padrão Django (email + senha)
  - Acesso total ao sistema

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

Crie um arquivo `.env`:

```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=America/Sao_Paulo
```

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
* Admin Django: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
* Painel Admin: [http://127.0.0.1:8000/login-admin/](http://127.0.0.1:8000/login-admin/)

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

## 📈 Status do Projeto

✅ Funcional
🚧 Sistema de notificações em desenvolvimento
🚀 Pronto para deploy em produção

---

## 💡 Próximos Passos

* Integração com WhatsApp (confirmação de agendamento)
* Notificações automáticas
* Interface mais interativa (JavaScript)
* Sistema de pagamentos

---

## 📄 Licença

Este projeto é de uso acadêmico / educacional.

---

## 👨‍💻 Autor

Desenvolvido por **Paulo Feitor**