# Arquitetura - Barbearia Agendamento Web

Este documento descreve a arquitetura e as principais decisões técnicas do sistema. Para instruções operacionais, variáveis de ambiente, comandos e procedimentos de migração, consulte [DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md).

## 1. Visão Geral

O sistema é uma aplicação web de agendamento para barbearias, construída como um monolito Django. Ele atende dois perfis:

- **Cliente:** autentica por e-mail/senha, agenda serviços, acompanha seus agendamentos e pode confirmar/cancelar por link.
- **Administrador:** gerencia clientes, profissionais, serviços, escalas e agendamentos.

Características principais:

- autenticação customizada com `ClienteUser`;
- cálculo dinâmico de disponibilidade;
- confirmação/cancelamento por link público com token;
- envio transacional de e-mails por provider configurável;
- histórico de tentativas de notificação;
- deploy no Render;
- PostgreSQL gerenciado na Neon.

URL pública de produção: https://barbearia-agendamento-web.onrender.com/

## 2. Decisões Arquiteturais

| Decisão | Motivo |
|---|---|
| Monolito Django | Simplicidade operacional e aderência ao tamanho do projeto |
| Apps por domínio | Separação clara entre clientes, agenda, serviços, profissionais e notificações |
| `ClienteUser` customizado | Autenticação por e-mail como identificador principal |
| Services explícitos | Isolar regras de negócio complexas das views |
| Signals para efeitos colaterais de agendamento | Invalidar cache e disparar confirmação sem espalhar lógica nas views |
| Provider de e-mail | Trocar SMTP/Brevo por configuração sem acoplar views ou services à Brevo |
| Cron externo no Render | Lembretes periódicos sem introduzir fila/task worker |
| PostgreSQL via `DATABASE_URL` | Mesma configuração para Render, Neon e ambiente local com PostgreSQL |

## 3. Componentes

```text
barbearia-agendamento-web/
├── apps/
│   ├── core/           # dashboards, backend admin por e-mail, mixins
│   ├── clientes/       # auth, clientes, verificação e reset de senha
│   ├── profissionais/  # profissionais e agenda semanal
│   ├── servicos/       # catálogo de serviços
│   ├── agendamentos/   # disponibilidade, reservas, tokens de confirmação
│   └── notificacoes/   # providers, envio de e-mail e NotificacaoLog
├── config/
│   ├── settings/       # base, dev, prod
│   ├── urls.py
│   └── wsgi.py
├── templates/
├── static/
├── requirements/
└── render.yaml
```

### Responsabilidades por Camada

| Camada | Local | Responsabilidade |
|---|---|---|
| Models | `*/models.py` | Entidades, relacionamentos e constraints |
| Forms | `*/forms.py` | Validação de entrada |
| Views | `*/views.py` | Orquestração HTTP, permissões e renderização |
| Services | `clientes/services.py` | Verificação de e-mail e reset de senha |
| Services | `agendamentos/services.py` | Disponibilidade e tokens de confirmação |
| Services | `notificacoes/services.py` | Renderização de templates e registro de notificações |
| Providers | `notificacoes/providers.py` | Transporte de e-mail por SMTP ou Brevo |
| Signals | `agendamentos/signals.py` | Invalidação de cache e confirmação automática |
| Templates | `templates/` | HTML da aplicação e e-mails |

## 4. Domínios

### Clientes e Autenticação

O sistema usa:

```python
AUTH_USER_MODEL = "clientes.ClienteUser"
```

Modelos principais:

- `ClienteUser`: usuário de autenticação, com `email` como `USERNAME_FIELD`.
- `Cliente`: perfil do cliente usado nos agendamentos.
- `VerificacaoEmail`: códigos de 6 dígitos para ativação da conta.

Backends:

- `AdminEmailBackend`: autenticação administrativa por e-mail.
- `ModelBackend`: backend padrão do Django.

O cliente só acessa dados próprios via mixins de autorização. Admins usam `is_staff=True`.

### Profissionais e Serviços

Modelos:

- `Profissional`: pessoa que atende.
- `ProfessionalSchedule`: grade semanal por profissional.
- `Servico`: serviço com duração e preço.

Esses modelos alimentam o cálculo de disponibilidade.

### Agendamentos

Modelos:

- `Agendamento`: vínculo entre cliente, profissional, serviço e data/hora.
- `TokenConfirmacaoAgendamento`: token para confirmar/cancelar por link público.

Status:

- `AGENDADO`
- `CONFIRMADO`
- `CANCELADO`
- `CONCLUIDO`

Índices relevantes:

- `data_hora_inicio`
- `status`
- `(profissional, data_hora_inicio)`

### Notificações

Modelos:

- `NotificacaoLog`: histórico de envios ligados a agendamentos.

Providers:

- `DjangoEmailProvider`: envio SMTP ou console backend.
- `BrevoEmailProvider`: envio transacional via `sib_api_v3_sdk`.

O restante do sistema conhece apenas `NotificacaoService`, não a Brevo diretamente.

## 5. Fluxos Principais

### Registro e Verificação

```text
ClienteRegisterView
→ cria ClienteUser(is_active=False) e Cliente
→ AuthService.gerar_e_enviar_codigo()
→ VerificacaoEmail
→ NotificacaoService.enviar_email_verificacao()
→ EmailProvider
```

```text
VerificarEmailView
→ AuthService.verificar_codigo()
→ marca código como usado
→ ativa ClienteUser
→ login automático
```

### Reset de Senha

```text
EsqueciSenhaView
→ AuthService.enviar_link_reset()
→ default_token_generator.make_token()
→ NotificacaoService.enviar_email_reset_senha()
→ EmailProvider
```

### Criação de Agendamento

```text
AgendamentoCreateView
→ valida form e disponibilidade
→ salva Agendamento(status=AGENDADO)
→ post_save signal
→ invalida cache
→ NotificacaoService.enviar_confirmacao_agendamento()
→ EmailProvider
→ NotificacaoLog
```

Falhas de e-mail não bloqueiam a criação do agendamento. Elas são registradas como `FALHOU` quando o fluxo envolve `NotificacaoLog`.

### Disponibilidade

```text
simple_final_availability / availability_api_view
→ AvailabilityService.get_available_slots()
→ ProfessionalSchedule
→ Agendamento(status in AGENDADO, CONFIRMADO)
→ subtrai horários ocupados e almoço
→ gera slots de 30 minutos
→ cache por 5 minutos
```

O cache é invalidado por signals em criação, atualização ou exclusão de agendamentos.

### Lembrete com Link

```text
Render Cron
→ python manage.py enviar_lembretes
→ busca agendamentos AGENDADO em D-3, D-1 e D-0
→ ConfirmacaoLinkService.obter_ou_criar_token()
→ NotificacaoService.enviar_lembrete_com_link()
→ EmailProvider
→ NotificacaoLog
```

```text
Cliente acessa /agendamentos/responder/<token>/
→ ResponderConfirmacaoView
→ ConfirmacaoLinkService.processar()
→ status = CONFIRMADO ou CANCELADO
→ token marcado como usado
→ signal invalida cache
```

## 6. Integrações Externas

### Brevo

Usada para e-mails transacionais em produção.

Decisão importante: o projeto usa a API transacional da Brevo, não campanhas de marketing.

```text
NotificacaoService
→ get_email_provider()
→ BrevoEmailProvider
→ TransactionalEmailsApi.send_transac_email()
```

O provider retorna um `EmailSendResult`, isolando o SDK da Brevo do restante da aplicação.

### Neon PostgreSQL

Banco PostgreSQL gerenciado. A aplicação acessa por `DATABASE_URL`.

Em produção, a conexão deve usar SSL (`DATABASE_SSL_REQUIRE=True` ou `sslmode=require` na URL).

### Render

Hospeda:

- Web Service Django/Gunicorn;
- Cron Job de lembretes.

URL pública do Web Service:

```text
https://barbearia-agendamento-web.onrender.com/
```

O Cron Job precisa das mesmas variáveis relevantes de banco, e-mail e `SITE_URL` do Web Service.

## 7. Infraestrutura e Configuração

### Banco

Regra arquitetural:

- `DATABASE_URL` definido: usar o banco apontado pela URL.
- `DATABASE_URL` vazio: fallback SQLite local.
- build do Render: SQLite temporário para não depender do banco no build.

### E-mail

Regra arquitetural:

- `EMAIL_PROVIDER=brevo`: Brevo transacional.
- `EMAIL_PROVIDER=smtp`: SMTP Django.
- `EMAIL_PROVIDER=brevo` sem chave em desenvolvimento: console backend.
- provider inválido: erro de configuração.
- Brevo sem chave/remetente em produção: erro de configuração.

### Static Files

WhiteNoise serve arquivos estáticos coletados por:

```text
python manage.py collectstatic --noinput
```

## 8. Qualidade e Testes

O projeto usa testes Django com `unittest`.

Coberturas existentes relevantes:

- testes de notificações;
- payload do provider Brevo;
- falha controlada de API;
- mascaramento de API key;
- criação de `NotificacaoLog` em sucesso/falha.

Pontos a ampliar:

- management command `enviar_lembretes`;
- reset de senha com provider mockado;
- verificação de e-mail com provider mockado;
- testes formais de settings.

## 9. Limitações e Riscos

| Risco / Limitação | Observação |
|---|---|
| Notificações síncronas | Envio acontece no fluxo da aplicação; para escala maior, considerar fila |
| Cache local em memória | `locmem` não é compartilhado entre múltiplos workers/instâncias |
| Cron sem fila | Simples e adequado ao projeto, mas menos robusto que task queue |
| Secrets em ambiente local | `.env` e dumps de banco não devem ser versionados |
| Credenciais expostas | Se connection string/API key aparecer em chat/log/documento, rotacionar |
| Cobertura de testes parcial | Fluxos principais funcionam, mas há espaço para ampliar testes automatizados |

## 10. Relação com Outros Documentos

- [../README.md](../README.md): visão geral, instalação local e uso básico.
- [DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md): documentação operacional completa.
- [FEATURES](FEATURES): histórico e critérios das features.
- [../architecture_diagram.md](../architecture_diagram.md): diagrama textual/visual complementar, quando atualizado.

## 11. Status Atual

Arquitetura atual validada com:

- autenticação por e-mail/senha;
- verificação de e-mail;
- reset de senha;
- agendamento e disponibilidade;
- confirmação/cancelamento por link;
- envio real via Brevo na Render;
- PostgreSQL migrado para Neon;
- DBML gerado para dbdiagram.io.

Pendências arquiteturais recomendadas:

- avaliar fila assíncrona caso o volume de e-mails cresça;
- avaliar cache compartilhado se houver múltiplas instâncias;
- manter `render.yaml` alinhado às variáveis atuais de Brevo e Neon;
- ampliar testes automatizados dos fluxos periódicos.
