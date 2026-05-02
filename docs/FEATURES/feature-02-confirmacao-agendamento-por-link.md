# Feature 02: Confirmação de Agendamento por Link com Hash

## 🎯 Contexto & Objetivo

Substituir o lembrete passivo do dia (`enviar_lembretes`) por um lembrete ativo com múltiplos disparos: o cliente recebe e-mails com link seguro (hash + expiração) nos dias configurados antes do agendamento e pode **confirmar** ou **cancelar** com um clique, sem precisar estar logado. Se o cliente já respondeu ao primeiro lembrete, os seguintes não são enviados.

Reutiliza o padrão de token com expiração introduzido em `feature-01` (`VerificacaoEmail`): token armazenado em banco, único por agendamento, reutilizado entre lembretes enquanto não usado.

> **Fora de escopo:** agendamentos com muita antecedência (ex.: 30+ dias). O intervalo máximo coberto é definido pela variável `LEMBRETE_DIAS_ANTECEDENCIA`. Agendamentos criados além desse horizonte receberão o primeiro lembrete quando o dia D-N mais distante chegar.

---

## 📐 Escopo Técnico

### Novo Model (`agendamentos/models.py`)

```python
class TokenConfirmacaoAgendamento(models.Model):
    agendamento  = models.OneToOneField(Agendamento, on_delete=CASCADE, related_name='token_confirmacao')
    token        = models.CharField(max_length=64, unique=True)   # secrets.token_urlsafe(48)
    expires_at   = models.DateTimeField()                          # = agendamento.data_hora_inicio
    usado_em     = models.DateTimeField(null=True, blank=True)
    acao         = models.CharField(max_length=20, null=True, blank=True,
                       choices=[('CONFIRMADO','Confirmado'),('CANCELADO','Cancelado')])

    class Meta:
        db_table = 'token_confirmacao_agendamento'
```

> **Expiração:** `expires_at = agendamento.data_hora_inicio`. O token deixa de ser válido no momento do próprio agendamento.

> **Reuso entre lembretes:** o mesmo token é enviado em todos os e-mails de lembrete do agendamento. Um novo token só é gerado se o anterior já foi usado (situação improvável, pois após o uso o agendamento muda de status e sai do filtro).

> **Analogia com feature-01:** `VerificacaoEmail` guarda `code` + `expires_at` + `is_used`. `TokenConfirmacaoAgendamento` segue o mesmo padrão, trocando código de 6 dígitos por token URL-safe e adicionando `acao` para registrar o que o cliente escolheu.

### Novo Service (`agendamentos/services.py` — classe adicional)

```python
class ConfirmacaoLinkService:

    @staticmethod
    def obter_ou_criar_token(agendamento) -> TokenConfirmacaoAgendamento:
        """
        Retorna token existente se ainda válido (não usado e não expirado).
        Gera novo token caso contrário.
        Garante que o mesmo link seja reutilizado em múltiplos lembretes.
        """

    @staticmethod
    def validar_token(token_str) -> TokenConfirmacaoAgendamento | None:
        """Retorna instância se válido (não usado e não expirado), None caso contrário."""

    @staticmethod
    def processar(token_obj, acao: str) -> Agendamento:
        """
        acao = 'CONFIRMADO' | 'CANCELADO'
        Transiciona status do agendamento, marca token como usado,
        invalida cache de disponibilidade via signal existente.
        """
```

### Alterações em `notificacoes/services.py`

Novo método público:

```python
@staticmethod
def enviar_lembrete_com_link(agendamento, link_confirmar, link_cancelar, dias_para_agendamento: int):
    """
    Lembrete com botões de ação. Registra NotificacaoLog tipo LEMBRETE_COM_LINK.
    dias_para_agendamento é passado ao template para personalizar a mensagem
    ('seu agendamento é hoje' vs 'seu agendamento é em 3 dias').
    """
```

### Alterações em `notificacoes/models.py`

Adicionar tipo ao `NotificacaoLog.Tipo`:

```python
LEMBRETE_COM_LINK = "LEMBRETE_COM_LINK", "Lembrete com Link de Confirmação"
```

### Novas URLs (`agendamentos/urls.py`)

| Método | URL | View |
|---|---|---|
| GET | `/agendamentos/responder/<str:token>/` | `ResponderConfirmacaoView` |
| POST | `/agendamentos/responder/<str:token>/` | `ResponderConfirmacaoView` |

### Nova View (`agendamentos/views.py`)

```python
class ResponderConfirmacaoView(View):
    """View pública (sem login). Exibe detalhes do agendamento e processa ação."""

    def get(self, request, token):
        token_obj = ConfirmacaoLinkService.validar_token(token)
        # token inválido/expirado/usado → render página de erro
        # token válido → render página de confirmação com dados do agendamento

    def post(self, request, token):
        token_obj = ConfirmacaoLinkService.validar_token(token)
        acao = request.POST.get('acao')  # 'CONFIRMADO' ou 'CANCELADO'
        # valida acao → ConfirmacaoLinkService.processar() → redirect com mensagem
```

### Alteração no Management Command (`enviar_lembretes.py`)

Lógica central — iterar sobre cada intervalo configurado:

```python
# settings.LEMBRETE_DIAS_ANTECEDENCIA = [3, 1, 0]  (padrão)
hoje = timezone.localdate()

for dias in settings.LEMBRETE_DIAS_ANTECEDENCIA:
    data_alvo = hoje + timedelta(days=dias)
    agendamentos = Agendamento.objects.filter(
        data_hora_inicio__date=data_alvo,
        status__in=[Agendamento.Status.AGENDADO],   # CONFIRMADO já respondeu, não precisa lembrar
    )
    for agendamento in agendamentos:
        token_obj = ConfirmacaoLinkService.obter_ou_criar_token(agendamento)
        link_base = f"{settings.SITE_URL}/agendamentos/responder/{token_obj.token}/"
        NotificacaoService.enviar_lembrete_com_link(
            agendamento,
            link_confirmar=link_base + "?acao=CONFIRMADO",
            link_cancelar=link_base + "?acao=CANCELADO",
            dias_para_agendamento=dias,
        )
```

> **Por que filtrar só `AGENDADO`?** Status `CONFIRMADO` significa que o cliente já respondeu positivamente — não precisa receber novo lembrete. Status `CANCELADO` e `CONCLUIDO` estão fora naturalmente.

> **Nota sobre URL absoluta:** O management command não tem `request`. Usar `settings.SITE_URL` (nova variável de ambiente) para montar a URL absoluta, igual a como `request.build_absolute_uri()` funciona nas views — mesma solução já documentada em `ARCHITECTURE.md` para `enviar_email_reset_senha`.

### Novo Template

| Arquivo | Descrição |
|---|---|
| `templates/notificacoes/email_lembrete_com_link.html` | E-mail com dados do agendamento + botão "Confirmar" + botão "Cancelar". Mensagem varia conforme `dias_para_agendamento` (hoje / em N dias) |
| `templates/agendamentos/responder_confirmacao.html` | Página de resposta: estado válido (mostra agendamento + form) ou estados de erro/já usado/expirado |

---

## 🔄 Fluxo de Dados

```
manage.py enviar_lembretes (cron 11:00 UTC, diário)
  → para cada intervalo em LEMBRETE_DIAS_ANTECEDENCIA (ex.: [3, 1, 0]):
      → filtra agendamentos com status=AGENDADO na data hoje+N
      → ConfirmacaoLinkService.obter_ou_criar_token(agendamento)
          → reutiliza token existente válido  ─┐ mesmo link
          → ou gera novo token                ─┘ em todos os lembretes
      → NotificacaoService.enviar_lembrete_com_link(...)
          → render email_lembrete_com_link.html
          → Gmail SMTP
          → NotificacaoLog(tipo=LEMBRETE_COM_LINK, status=ENVIADO)

Cliente clica no link do e-mail (qualquer dos lembretes)
  → GET /agendamentos/responder/<token>/
      → ConfirmacaoLinkService.validar_token(token)
      → render responder_confirmacao.html (dados + botões)

  → POST /agendamentos/responder/<token>/ {acao: CONFIRMADO | CANCELADO}
      → ConfirmacaoLinkService.processar(token_obj, acao)
          → Agendamento.status = acao
          → token_obj.usado_em = now(), token_obj.acao = acao
          → post_save signal → invalida cache de disponibilidade
      → redirect com django.contrib.messages (sucesso)
      → próximos lembretes não são enviados (agendamento saiu do filtro status=AGENDADO)
```

---

## 🔒 Segurança & Validações

| Cenário | Comportamento |
|---|---|
| Token inexistente | HTTP 200 com página de erro "Link inválido" (não 404, evita enumeração) |
| Token expirado (`now > expires_at`) | Página de erro "Agendamento já passou" |
| Token já usado | Página informativa "Você já respondeu: {acao}" |
| `acao` POST inválida | `400 Bad Request` |
| Agendamento já `CANCELADO` ou `CONCLUIDO` | Página informativa, sem alterar status |

---

## ⚙️ Novas Variáveis de Ambiente

| Variável | Descrição | Padrão | Exemplo |
|---|---|---|---|
| `SITE_URL` | URL base para links em e-mails enviados fora de requests HTTP | — | `https://barbearia-agendamento-web.onrender.com` |
| `LEMBRETE_DIAS_ANTECEDENCIA` | Intervalos de envio em dias, separados por vírgula | `3,1,0` | `7,3,1,0` |

Localmente: `SITE_URL=http://127.0.0.1:8000` e `LEMBRETE_DIAS_ANTECEDENCIA=3,1,0` no `.env`.

`settings.py` faz o parse:
```python
LEMBRETE_DIAS_ANTECEDENCIA = [
    int(d) for d in config("LEMBRETE_DIAS_ANTECEDENCIA", default="3,1,0").split(",")
]
```

---

## ✅ Critérios de Aceite

- [ ] `TokenConfirmacaoAgendamento` criado via migração; `db_table = 'token_confirmacao_agendamento'`.
- [ ] `manage.py enviar_lembretes` itera sobre `LEMBRETE_DIAS_ANTECEDENCIA` e envia e-mail para cada intervalo com agendamentos `AGENDADO` (verificar no console em dev).
- [ ] Agendamento com status `CONFIRMADO` ou `CANCELADO` não recebe novo lembrete.
- [ ] O mesmo token é reutilizado em lembretes subsequentes do mesmo agendamento.
- [ ] GET `/agendamentos/responder/<token>/` exibe dados corretos do agendamento.
- [ ] POST com `acao=CONFIRMADO` transiciona status `AGENDADO → CONFIRMADO` e marca token usado.
- [ ] POST com `acao=CANCELADO` transiciona status para `CANCELADO` e marca token usado.
- [ ] Token expirado ou já usado renderiza página informativa sem erro 500.
- [ ] `NotificacaoLog` registra entrada `LEMBRETE_COM_LINK` para cada envio.
- [ ] Cache de disponibilidade invalidado via signal existente após qualquer transição de status.
- [ ] View `ResponderConfirmacaoView` não requer login (acessível sem sessão ativa).
- [ ] `.env.example` e `ARCHITECTURE.md` atualizados com `SITE_URL`, `LEMBRETE_DIAS_ANTECEDENCIA` e novo fluxo.

---

## 📁 Arquivos a Criar / Modificar

| Ação | Arquivo |
|---|---|
| Criar | `apps/agendamentos/migrations/XXXX_token_confirmacao_agendamento.py` |
| Modificar | `apps/agendamentos/models.py` — adicionar `TokenConfirmacaoAgendamento` |
| Modificar | `apps/agendamentos/services.py` — adicionar `ConfirmacaoLinkService` |
| Modificar | `apps/agendamentos/views.py` — adicionar `ResponderConfirmacaoView` |
| Modificar | `apps/agendamentos/urls.py` — nova rota `responder/<str:token>/` |
| Modificar | `apps/notificacoes/models.py` — adicionar `LEMBRETE_COM_LINK` ao `Tipo` |
| Modificar | `apps/notificacoes/services.py` — adicionar `enviar_lembrete_com_link()` |
| Modificar | `apps/notificacoes/management/commands/enviar_lembretes.py` — iterar por intervalo, usar `ConfirmacaoLinkService` |
| Modificar | `config/settings/base.py` — adicionar `LEMBRETE_DIAS_ANTECEDENCIA` |
| Criar | `templates/notificacoes/email_lembrete_com_link.html` |
| Criar | `templates/agendamentos/responder_confirmacao.html` |
| Modificar | `.env.example` — adicionar `SITE_URL` e `LEMBRETE_DIAS_ANTECEDENCIA` |
| Modificar | `ARCHITECTURE.md` — atualizar fluxo de lembrete e variáveis de ambiente |

---

## ⚠️ Impacto na Arquitetura Atual

- `enviar_lembretes` continua sendo o ponto de entrada (cron Render, ou `python manage.py enviar_lembretes` localmente).
- O signal `post_save` de `Agendamento` já invalida o cache — nenhuma alteração necessária.
- `ResponderConfirmacaoView` é pública: não usa `ClienteRequiredMixin` nem `AdminRequiredMixin`.
- Nenhum campo existente em `Agendamento` é removido; `confirmado_whatsapp` pode ser depreciado futuramente (fora do escopo desta feature).
