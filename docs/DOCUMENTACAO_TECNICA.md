# Documentação Técnica - PI Barbearia

## 1. Visão Geral do Sistema

**Nome do Projeto**: PI Barbearia  
**Objetivo Principal**: Sistema completo de agendamento online para barbearias  
**Problema que Resolve**: Gerenciamento automatizado de agendamentos, controle de disponibilidade de profissionais e organização do fluxo de clientes em barbearias  
**Tipo de Sistema**: Aplicação web de agendamento com dashboard administrativo  
**Público-alvo**: Donos de barbearias, profissionais barbeiros e clientes finais  

O sistema oferece uma interface simplificada para clientes realizarem agendamentos por telefone e um painel administrativo completo para gestão do negócio.

---

## 2. Arquitetura do Projeto

**Tipo de Arquitetura**: Monolito Django seguindo padrão MVT (Model-View-Template)  
**Organização Geral**: Estrutura modular com apps Django para cada domínio de negócio  
**Separação de Responsabilidades**: Cada app Django possui responsabilidade clara e definida  
**Padrões Identificados**: Class-Based Views (CBV), Mixins de autenticação, Services Layer para lógica complexa  

A arquitetura segue as melhores práticas Django com separação clara entre:
- Models: Definição de dados e regras de negócio
- Views: Lógica de apresentação e controle de acesso
- Templates: Camada de visualização
- Services: Lógica de negócio complexa (disponibilidade de horários)

---

## 3. Estrutura de Diretórios

### `/`
- **manage.py**: Entry point do Django, configurado para ambiente de desenvolvimento
- **render.yaml**: Configuração de deploy na plataforma Render
- **requirements.txt**: Dependências do projeto
- **README.md**: Documentação principal

### `/config`
- **settings/**: Configurações modularizadas (base.py, dev.py, prod.py)
- **urls.py**: URLs principais do projeto
- **wsgi.py/asgi.py**: Configurações de servidor web

### `/apps`
Diretório principal contendo todos os aplicativos Django:
- **core/**: App central (autenticação, dashboards, navegação)
- **clientes/**: Gestão de clientes
- **profissionais/**: Gestão de profissionais e escalas
- **servicos/**: Catálogo de serviços
- **agendamentos/**: Sistema de agendamentos
- **notificacoes/**: Sistema de notificações (em desenvolvimento)

### `/templates`
Templates HTML organizados por app:
- **base.html**: Template base com navegação e estrutura comum
- **core/**: Templates de autenticação e dashboards
- **clientes/**: Templates de CRUD de clientes
- **agendamentos/**: Templates de agendamentos

### `/static`
Arquivos estáticos:
- **css/styles.css**: Estilos CSS minificados

### `/requirements`
Arquivos de dependências:
- **base.txt**: Dependências principais
- **dev.txt**: Dependências de desenvolvimento
- **prod.txt**: Dependências de produção

---

## 4. Apps Django

### apps/core
**Responsabilidade**: Autenticação, navegação e dashboards  
**Principais Arquivos**:
- `views.py`: Views principais de autenticação e dashboards
- `backends.py`: Backends customizados de autenticação
- `mixins.py`: Mixins de controle de acesso
- `urls.py`: URLs principais e administrativas

**Relação com outros apps**: Orquestra o fluxo principal e autenticação  
**Papel no sistema**: Ponto de entrada e controle de acesso centralizado

### apps/clientes
**Responsabilidade**: Gestão de clientes  
**Principais Arquivos**:
- `models.py`: Modelo Cliente com validação de telefone/email únicos
- `views.py`: CRUD de clientes e "meus dados" para clientes
- `forms.py`: Formulários de cadastro e edição

**Relação com outros apps**: Integra com agendamentos (FK)  
**Papel no sistema**: Gerenciamento do cadastro de clientes

### apps/profissionais
**Responsabilidade**: Gestão de profissionais e escalas de trabalho  
**Principais Arquivos**:
- `models.py`: Profissional e ProfessionalSchedule (escalas semanais)
- `views.py`: CRUD de profissionais
- `forms.py`: Formulários com validação complexa de horários

**Relação com outros apps**: FK em agendamentos, usado no sistema de disponibilidade  
**Papel no sistema**: Controle de quem pode atender e quando

### apps/servicos
**Responsabilidade**: Catálogo de serviços oferecidos  
**Principais Arquivos**:
- `models.py`: Servico com duração e preço
- `views.py`: CRUD de serviços
- `forms.py`: Formulários de serviços

**Relação com outros apps**: FK em agendamentos, usado no cálculo de disponibilidade  
**Papel no sistema**: Define o que é oferecido e quanto tempo cada serviço dura

### apps/agendamentos
**Responsabilidade**: Sistema completo de agendamentos  
**Principais Arquivos**:
- `models.py`: Agendamento com status e confirmações
- `views.py`: CRUD com permissões diferenciadas (admin/cliente)
- `services.py`: AvailabilityService para cálculo de horários disponíveis
- `forms.py`: Formulários com validação de disponibilidade

**Relação com outros apps**: Integra clientes, profissionais e serviços  
**Papel no sistema**: Core business - agendamento de serviços

### apps/notificacoes
**Responsabilidade**: Sistema de notificações (em desenvolvimento)  
**Principais Arquivos**:
- `models.py`: Vazio (em desenvolvimento)

**Relação com outros apps**: Não integrado ainda  
**Papel no sistema**: Futuro sistema de notificações

---

## 5. Fluxo da Aplicação

### Fluxo Principal (Cliente)
```
request → HomeView → Verifica sessão
├── Cliente logado → ClienteDashboard → Lista agendamentos
├── Admin logado → Redirect para AdminDashboard
└── Não logado → Redirect para login_cliente
```

### Fluxo de Login Cliente
```
POST /login-cliente/ → ClienteLoginView
├── Telefone encontrado → Seta cliente_id na sessão → Home
└── Telefone não encontrado → Seta telefone_cadastro → clientes_create
```

### Fluxo de Agendamento
```
GET /agendamentos/create/ → AgendamentoCreateView
├── Cliente: Filtra opções e predefine cliente
└── Admin: Acesso total a todas opções

POST → Valida disponibilidade → Salva → Redirect
```

### Fluxo de Disponibilidade
```
GET /agendamentos/availability/?professional_id=X&service_id=Y
→ availability_api_view → AvailabilityService.get_available_slots()
→ Calcula horários livres considerando:
  - Escala do profissional
  - Agendamentos existentes
  - Horário de almoço
  - Tempo de serviço
→ JSON com horários disponíveis paginados
```

---

## 6. Models (Dados)

### Entidades Principais

#### Cliente
- **nome**: CharField(100) - Nome completo
- **telefone**: CharField(20, unique=True) - Telefone para login
- **email**: EmailField(unique=True) - Email único
- **created_at**: DateTimeField(auto_now_add=True)

#### Profissional
- **nome**: CharField(100) - Nome do profissional
- **ativo**: BooleanField(default=True) - Status ativo/inativo
- **created_at**: DateTimeField(auto_now_add=True)

#### ProfessionalSchedule (Escalas)
- **profissional**: FK(Profissional) - Relacionamento
- **weekday**: IntegerChoices - Dia da semana (0-6)
- **start_time**: TimeField - Início do expediente
- **end_time**: TimeField - Fim do expediente
- **lunch_start/lunch_end**: TimeField(null=True) - Horário de almoço
- **is_day_off**: BooleanField(default=False) - Dia de folga

#### Servico
- **nome**: CharField(100) - Nome do serviço
- **duracao_minutos**: PositiveIntegerField - Duração em minutos
- **preco**: DecimalField(10,2, null=True) - Preço opcional

#### Agendamento
- **cliente**: FK(Cliente) - Cliente do agendamento
- **profissional**: FK(Profissional) - Profissional que atenderá
- **servico**: FK(Servico) - Serviço contratado
- **data_hora_inicio**: DateTimeField - Início do atendimento
- **status**: TextChoices - AGENDADO/CONFIRMADO/CANCELADO/CONCLUIDO
- **confirmado_whatsapp**: BooleanField(default=False) - Confirmação via WhatsApp

### Relacionamentos
- Cliente → Agendamentos (OneToMany)
- Profissional → Agendamentos (OneToMany)
- Servico → Agendamentos (OneToMany)
- Profissional → ProfessionalSchedule (OneToMany)

### Índices Importantes
- Agendamento: data_hora_inicio, status, (profissional, data_hora_inicio)
- ProfessionalSchedule: (profissional, weekday)

---

## 7. Views / Lógica de Negócio

### Tipos de Views
- **100% Class-Based Views (CBV)**: ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView
- **Mixins de Autenticação**: ClienteRequiredMixin, AdminRequiredMixin, AdminOrClienteMixin
- **API Endpoints**: availability_api_view (JSON response)

### Organização da Lógica
- **Views simples**: CRUD básico em cada app
- **Views complexas**: HomeView com lógica de redirecionamento
- **Services Layer**: AvailabilityService para lógica complexa de disponibilidade

### Regras Importantes
- **Clientes**: Acesso apenas aos próprios agendamentos
- **Admins**: Acesso total a todos os recursos
- **Disponibilidade**: Cálculo complexo considerando múltiplos fatores
- **Sessão**: Clientes usam sessão customizada (cliente_id)

---

## 8. Templates e Frontend

### Organização dos Templates
- **base.html**: Template base com navegação condicional
- **Herança**: Todos os templates herdam de base.html
- **Estrutura por app**: Templates organizados em subdiretórios por app

### Navegação Condicional
O template base implementa menus diferentes:
- **Cliente logado**: Início, Novo Agendamento, Meus Agendamentos, Meus Dados
- **Admin logado**: Painel, Clientes, Profissionais, Serviços, Agendamentos, Django Admin
- **Público**: Área do Cliente, Acesso Admin (discreto)

### Integração com Backend
- **Context Processors**: auth, messages, request
- **Messages Framework**: Feedback de ações do usuário
- **CSRF Protection**: Ativo em todos os formulários
- **Static Files**: CSS minificado em único arquivo

---

## 9. Static Files

### Organização
- **/static/css/styles.css**: Único arquivo CSS, minificado
- **Configuração**: STATIC_URL="/static/", STATIC_ROOT="staticfiles"
- **Middleware**: WhiteNoise para servir arquivos estáticos

### Estilos Implementados
- Design responsivo com media queries
- Cores consistentes (header #333, botões #0d6efd)
- Grid system para layouts
- Formulários estilizados
- Messages com cores por tipo (sucesso/erro)

---

## 10. Configurações (Settings)

### Estrutura Modular
- **base.py**: Configurações compartilhadas
- **dev.py**: Configurações de desenvolvimento
- **prod.py**: Configurações de produção

### Variáveis Importantes
- **SECRET_KEY**: Via variável de ambiente
- **DEBUG**: Controlado por variável de ambiente
- **ALLOWED_HOSTS**: Configurável via variável de ambiente
- **TIME_ZONE**: "America/Sao_Paulo"

### Configurações de Segurança
- **WhiteNoise**: Middleware para arquivos estáticos
- **CSRF Protection**: Ativo por padrão
- **SecurityMiddleware**: Headers de segurança
- **Custom Auth Backends**: Backend customizado para clientes

---

## 11. Autenticação e Segurança

### Sistema Dual de Autenticação
O sistema implementa dois sistemas de autenticação paralelos:

#### Autenticação de Clientes
- **Método**: Login por telefone (sem senha)
- **Backend**: TelefoneBackend (customizado)
- **Sessão**: Usa `request.session['cliente_id']`
- **Mixin**: ClienteRequiredMixin
- **Fluxo**: Telefone → Verificação → Sessão customizada

#### Autenticação de Administradores
- **Método**: Email + senha padrão Django
- **Backend**: AdminEmailBackend (customizado)
- **Sessão**: Sistema padrão Django
- **Mixin**: AdminRequiredMixin
- **Requisito**: user.is_staff=True

### Controle de Acesso
- **Clientes**: Acesso apenas aos próprios dados e agendamentos
- **Admins**: Acesso total a todos os recursos
- **Proteção**: Todos os endpoints protegidos por mixins apropriados
- **Redirecionamento**: URLs de login específicas por tipo de usuário

### Segurança Implementada
- **CSRF Tokens**: Ativo em todos os formulários
- **Session Security**: Configurações seguras de sessão
- **Password Hashing**: Padrão Django
- **XSS Protection**: Templates escapados por padrão

---

## 12. Integrações Externas

### APIs Externas
- **WhatsApp**: Campo `confirmado_whatsapp` sugere integração futura
- **Render**: Plataforma de deploy configurada

### Serviços de Terceiros
- **Render Hosting**: Configurado via render.yaml
- **PostgreSQL**: Banco de dados em produção (via dj-database-url)
- **Gunicorn**: Web server em produção

### Dependências Externas
- **dj-database-url**: Gerenciamento de conexões de banco
- **WhiteNoise**: Servidor de arquivos estáticos
- **python-decouple**: Gestão de variáveis de ambiente

---

## 13. Dependências do Projeto

### Bibliotecas Principais (requirements/base.txt)
- **Django>=5.1,<6.1**: Framework web principal
- **dj-database-url>=2.2.0**: Configuração de banco de dados via URL
- **gunicorn>=23.0.0**: WSGI server para produção
- **psycopg[binary]>=3.2.0**: Driver PostgreSQL
- **whitenoise>=6.7.0**: Servidor de arquivos estáticos
- **python-decouple>=3.8**: Gestão de variáveis de ambiente

### Função no Sistema
- **Django**: Framework principal MVC/MVT
- **dj-database-url**: Abstração de configuração de banco (dev/prod)
- **gunicorn**: Servidor web para produção (Render)
- **psycopg**: Conexão com PostgreSQL em produção
- **whitenoise**: Otimização de static files
- **python-decouple**: Segurança na gestão de secrets

---

## 14. Como Rodar o Projeto

### 1. Instalar Dependências
```bash
pip install -r requirements/dev.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
cp .env.example .env
# Editar .env com suas configurações:
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=America/Sao_Paulo
```

### 3. Rodar Migrações
```bash
python manage.py migrate
```

### 4. Criar Superusuário
```bash
python manage.py createsuperuser
# Ou usar variáveis de ambiente para criação automática
```

### 5. Subir Servidor de Desenvolvimento
```bash
python manage.py runserver
```

### 6. Acessar Aplicação
- **Principal**: http://127.0.0.1:8000/
- **Admin Django**: http://127.0.0.1:8000/admin/
- **Admin Dashboard**: http://127.0.0.1:8000/login-admin/

---

## 15. Pontos Fortes da Arquitetura

### Estrutura Modular
- **Separação clara** de responsabilidades por app Django
- **Consistência** nos padrões de CRUD e views
- **Organização** lógica de templates e static files

### Autenticação Dual
- **Solução elegante** para dois tipos de usuários distintos
- **Segurança** com backends customizados
- **Experiência simplificada** para clientes (login por telefone)

### Sistema de Disponibilidade
- **Algoritmo robusto** considerando múltiplos fatores
- **Cache inteligente** para performance
- **API RESTful** para integração frontend

### Boas Práticas Django
- **Class-Based Views** para reuso de código
- **Mixins de autenticação** para DRY
- **Settings modularizadas** para ambientes diferentes
- **Proper indexing** nos modelos para performance

### Deploy Production-Ready
- **Configuração Render** completa
- **WhiteNoise** para static files
- **PostgreSQL** para produção
- **Variáveis de ambiente** para segurança

---

## 16. Pontos de Atenção

### Complexidade de Autenticação
- **Sistema dual** pode gerar confusão para novos desenvolvedores
- **Sessão customizada** requer cuidado com concorrência
- **Backends customizados** aumentam complexidade de manutenção

### Acoplamento
- **Views com lógica específica** de usuário (cliente vs admin)
- **Services layer** poderia ser mais abstraído
- **Templates com múltiplas condições** de navegação

### Frontend Limitado
- **CSS minificado** dificulta customização
- **JavaScript ausente** para interações mais ricas
- **Design responsivo** básico

### Escalabilidade
- **Monolito Django** pode limitar crescimento
- **Cache simples** pode não ser suficiente para alta carga
- **Banco de dados centralizado** pode ser bottleneck

### Segurança
- **Login sem senha** para clientes pode ser preocupante
- **Validação de telefone** implementada mas não robusta
- **Logs de acesso** não implementados

---

## 17. Conclusão

### Resumo Técnico
O PI Barbearia é um sistema web completo de agendamento desenvolvido em Django 5.1+ com arquitetura monolítica bem estruturada. Implementa um sistema dual de autenticação (clientes por telefone, administradores por email/senha) e um algoritmo sofisticado para cálculo de disponibilidade de horários.

### Nível de Maturidade
**Alto** - O sistema demonstra:
- Arquitetura bem planejada com separação clara de responsabilidades
- Implementação completa de CRUD para todas as entidades
- Sistema de autenticação robusto e customizado
- Algoritmos complexos para business logic (disponibilidade)
- Configuração completa para deploy em produção

### Facilidade de Manutenção
**Boa** - Fatores positivos:
- Código organizado e documentado
- Padrões consistentes em todo o projeto
- Configurações modularizadas
- Tests structure presente (embora não detalhado nesta análise)
- Deploy automatizado configurado

### Recomendações para Evolução
1. **Implementar frontend mais rico** (JavaScript framework)
2. **Adicionar sistema de notificações** (app notificacoes)
3. **Implementar testes automatizados** abrangentes
4. **Considerar microserviços** para escalabilidade
5. **Adicionar analytics e logging** para monitoramento
6. **Implementar validação de telefone** (SMS/WhatsApp)
7. **Adicionar integrações de pagamento**

O sistema está pronto para produção e serve como excelente base para evolução, com arquitetura sólida e boas práticas implementadas.
