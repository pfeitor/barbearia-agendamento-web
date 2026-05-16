# Feature 03: Troca do Envio de E-mail de SMTP para API Brevo

## Status da implementacao

**Status:** implementacao tecnica concluida e validada localmente com Brevo.

**Data de atualizacao:** 2026-05-16.

**Resumo do que foi entregue:**

- Provider configuravel por `EMAIL_PROVIDER=smtp` ou `EMAIL_PROVIDER=brevo`.
- SDK `sib-api-v3-sdk` adicionado aos requirements.
- `BrevoEmailProvider` usando API transacional (`TransactionalEmailsApi.send_transac_email`).
- Fallback local para console quando `EMAIL_PROVIDER=brevo` esta sem `API_KEY_BREVO` em desenvolvimento.
- `NotificacaoService` integrado ao provider para confirmacao de agendamento, lembretes, verificacao de e-mail e reset de senha.
- `NotificacaoLog` expandido com `provider` e `provider_message_id`.
- `.env.example`, `README.md` e `ARCHITECTURE.md` atualizados.
- Testes unitarios adicionados para provider Brevo e integracao basica com `NotificacaoService`.

**Validacoes executadas:**

```bash
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py check
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py test apps.notificacoes.tests
$env:DEBUG='True'; .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Resultados:

- `manage.py check`: OK.
- `apps.notificacoes.tests`: 5 testes OK.
- `makemigrations --check --dry-run`: sem mudancas pendentes.
- Import do SDK `sib_api_v3_sdk`: OK apos instalar dependencias na `.venv`.
- Smoke local de reset de senha com `EMAIL_PROVIDER=brevo`: OK.

Observacao local: durante o primeiro teste real, o envio falhou com `No module named 'sib_api_v3_sdk'` porque a dependencia ainda nao estava instalada na `.venv`. A instalacao via `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` corrigiu o ambiente local.

**Pendencias fora do ambiente local:**

- Configurar variaveis reais no Render.
- Executar smoke real com envio via Brevo.
- Conferir evento de envio/entrega no painel Brevo.
- Opcional: ampliar testes para management command `enviar_lembretes`, reset de senha e verificacao de e-mail com provider mockado.

## Contexto e objetivo

Migrar o envio dos e-mails transacionais ja existentes no sistema de SMTP para API HTTP da Brevo, usando a chave `API_KEY_BREVO` configurada no `.env`. O objetivo e reduzir falhas de conexao SMTP em producao e manter exatamente os mesmos fluxos, templates e destinatarios atuais.

O mecanismo de envio deve ser configuravel por ambiente via `.env`, permitindo alternar entre `smtp` e `brevo` sem alterar codigo.

O foco principal e o e-mail de confirmacao de agendamento disparado pela aplicacao. A mesma troca de transporte pode ser aplicada aos demais e-mails ja construidos no `NotificacaoService`, sem criar novos tipos de contato por e-mail.

O exemplo informado usa `EmailCampaignsApi.create_email_campaign`, que serve para campanhas de marketing. Para este projeto, a implementacao deve usar a API transacional da Brevo (`TransactionalEmailsApi.send_transac_email` no SDK `sib_api_v3_sdk`). Criacao de campanhas, listas de contatos e qualquer fluxo de marketing estao fora de escopo.

## Escopo funcional

### Incluido

- Trocar o mecanismo de envio de SMTP para API Brevo.
- Permitir selecionar o mecanismo de envio pelo `.env`: `EMAIL_PROVIDER=smtp` ou `EMAIL_PROVIDER=brevo`.
- Preservar os templates HTML e textos ja existentes.
- Preservar os destinatarios ja definidos pela aplicacao.
- Preservar `NotificacaoLog` como historico de sucesso/falha.
- Priorizar o envio de confirmacao de agendamento.
- Permitir que os demais e-mails transacionais ja existentes usem o mesmo provider, sem mudanca funcional.

### Nao incluido

- Criar campanhas Brevo.
- Criar, importar ou sincronizar listas de contatos.
- Criar novos tipos de e-mail.
- Criar novos templates de marketing.
- Enviar newsletter, propaganda ou comunicacao fora dos fluxos atuais.
- Capturar contatos que nao sejam os clientes envolvidos nos fluxos atuais da aplicacao.

## Escopo tecnico

### Dependencias

Adicionar o SDK oficial usado no exemplo:

```txt
sib-api-v3-sdk
```

### Variaveis de ambiente

| Variavel | Obrigatoria | Descricao | Exemplo |
|---|---:|---|---|
| `API_KEY_BREVO` | Sim em producao | Chave da API Brevo. Nunca deve ser commitada. | `xkeysib-...` |
| `EMAIL_PROVIDER` | Nao | Provider ativo. Valores aceitos: `smtp` ou `brevo`. | `brevo` |
| `SMTP_EMAIL_HOST_USER` | Sim quando `EMAIL_PROVIDER=smtp` | Usuario/remetente autenticado no servidor SMTP. Substitui `EMAIL_HOST_USER`. | `seuemail@gmail.com` |
| `SMTP_EMAIL_HOST_PASSWORD` | Sim quando `EMAIL_PROVIDER=smtp` | Senha/app password do servidor SMTP. Substitui `EMAIL_HOST_PASSWORD`. | `xxxx-xxxx-xxxx-xxxx` |
| `BREVO_SENDER_NAME` | Sim em producao | Nome exibido no remetente. | `Minha Barbearia` |
| `BREVO_SENDER_EMAIL` | Sim em producao | E-mail remetente validado na Brevo. | `noreply@seudominio.com` |
| `DEFAULT_FROM_EMAIL` | Sim | Compatibilidade com os templates e services atuais. | `Minha Barbearia <noreply@seudominio.com>` |
| `BREVO_TIMEOUT` | Nao | Timeout de chamada HTTP, em segundos. | `10` |

Exemplo SMTP:

```env
EMAIL_PROVIDER=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
SMTP_EMAIL_HOST_USER=seuemail@gmail.com
SMTP_EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=Minha Barbearia <seuemail@gmail.com>
```

Exemplo Brevo API:

```env
EMAIL_PROVIDER=brevo
API_KEY_BREVO=xkeysib-...
BREVO_SENDER_NAME=Minha Barbearia
BREVO_SENDER_EMAIL=noreply@seudominio.com
DEFAULT_FROM_EMAIL=Minha Barbearia <noreply@seudominio.com>
```

### Arquivos previstos

| Acao | Arquivo |
|---|---|
| Modificar | `requirements.txt` ou arquivo de requirements usado no deploy |
| Modificar | `.env.example` |
| Modificar | `config/settings/base.py` |
| Criar | `apps/notificacoes/providers.py` |
| Modificar | `apps/notificacoes/services.py` |
| Modificar | `apps/notificacoes/models.py` se for necessario guardar `provider` ou `message_id` |
| Criar/Modificar | testes em `apps/notificacoes/tests.py` ou pacote equivalente |
| Modificar | `README.md` e/ou `ARCHITECTURE.md` apos a implementacao |

### Desenho proposto

Criar uma camada pequena de provider para isolar a Brevo do restante da aplicacao:

```python
class EmailProvider:
    def send(self, *, to_email, to_name, subject, html_body, text_body=None) -> EmailSendResult:
        ...


class BrevoEmailProvider(EmailProvider):
    """Envia e-mail transacional via API Brevo."""
```

`NotificacaoService` continua sendo o ponto de entrada dos casos de uso. Ele renderiza os templates existentes, chama o provider ativo e registra `NotificacaoLog`.

Nenhuma view, formulario ou regra de negocio deve passar a conhecer diretamente a Brevo. A mudanca deve ficar concentrada na camada de notificacoes.

## Fase 1: Configuracao e dependencia

### Entregaveis

- SDK `sib-api-v3-sdk` adicionado aos requirements.
- `config/settings/base.py` lendo `EMAIL_PROVIDER` e carregando as configuracoes correspondentes a `smtp` ou `brevo`.
- Configuracoes SMTP preservadas para `EMAIL_PROVIDER=smtp`, usando nomes mais claros no `.env`.
- Renomear as variaveis SMTP:
  - `EMAIL_HOST_USER` -> `SMTP_EMAIL_HOST_USER`;
  - `EMAIL_HOST_PASSWORD` -> `SMTP_EMAIL_HOST_PASSWORD`.
- Configuracoes Brevo adicionadas para `EMAIL_PROVIDER=brevo`: `API_KEY_BREVO`, `BREVO_SENDER_NAME`, `BREVO_SENDER_EMAIL` e `BREVO_TIMEOUT`.
- `.env.example` atualizado com placeholders, sem valores reais.
- Fail-fast em producao quando `EMAIL_PROVIDER=brevo` e `API_KEY_BREVO` ou remetente estiverem ausentes.
- Fail-fast quando `EMAIL_PROVIDER` tiver valor diferente de `smtp` ou `brevo`.
- Ambiente de desenvolvimento mantendo console backend ou provider fake quando `API_KEY_BREVO` nao estiver definida.

### Criterios de aceite

- [x] A aplicacao inicia localmente sem `API_KEY_BREVO` quando `DEBUG=True`.
- [x] `EMAIL_PROVIDER=smtp` usa o envio SMTP atual.
- [x] `EMAIL_PROVIDER=smtp` le `SMTP_EMAIL_HOST_USER` e `SMTP_EMAIL_HOST_PASSWORD`.
- [x] `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` deixam de ser os nomes documentados no `.env.example`.
- [x] `EMAIL_PROVIDER=brevo` usa a API transacional da Brevo.
- [x] `EMAIL_PROVIDER` invalido gera erro claro de configuracao.
- [x] Em producao, `EMAIL_PROVIDER=brevo` sem `API_KEY_BREVO` gera erro claro de configuracao.
- [x] `.env` nao e alterado nem commitado.
- [x] `.env.example` documenta `API_KEY_BREVO` apenas com placeholder.
- [x] `python manage.py check` executa sem erros com configuracao local.

### Testes

- [x] Validacao manual de settings: `EMAIL_PROVIDER=brevo` sem chave em desenvolvimento inicia com console backend.
- [x] Validacao manual de settings: `EMAIL_PROVIDER` invalido gera `ImproperlyConfigured`.
- [x] Validacao manual de settings: `EMAIL_PROVIDER=brevo` sem chave/remetente em `config.settings.prod` gera `ImproperlyConfigured`.
- [x] Smoke test: `python manage.py check`.
- [ ] Unitarios formais de settings podem ser adicionados em uma rodada posterior, se necessario.

## Fase 2: Provider Brevo transacional

### Entregaveis

- `BrevoEmailProvider` com inicializacao do SDK usando `API_KEY_BREVO`.
- Metodo `send()` aceitando destinatario, assunto, HTML e texto puro.
- Conversao do retorno da Brevo para um resultado interno com `success`, `message_id`, `provider` e `raw_response` resumido.
- Tratamento de `ApiException`, timeout e excecoes inesperadas.
- Logs tecnicos sem expor `API_KEY_BREVO`, payload completo ou dados sensiveis desnecessarios.

### Criterios de aceite

- [x] Provider monta `SendSmtpEmail` com remetente, destinatario, assunto, `html_content` e `text_content`.
- [x] Provider retorna sucesso quando o SDK responde sem excecao.
- [x] Provider retorna falha controlada quando o SDK levanta `ApiException`.
- [x] Nenhum log contem a chave `API_KEY_BREVO`.
- [x] Chamadas reais a Brevo nao ocorrem em testes automatizados.

### Testes

- [x] Unitario com mock de `sib_api_v3_sdk.TransactionalEmailsApi`.
- [x] Unitario validando payload enviado ao SDK.
- [x] Unitario simulando `ApiException` e verificando resultado de falha.
- [x] Unitario garantindo que a API key nao aparece no erro retornado/logado.

## Fase 3: Integracao com `NotificacaoService`

### Entregaveis

- `NotificacaoService._enviar_email()` usando provider ativo quando `EMAIL_PROVIDER=brevo`.
- `NotificacaoService._enviar_email()` mantendo envio SMTP quando `EMAIL_PROVIDER=smtp`.
- Fluxos existentes preservados, sem criar novos tipos de contato:
  - confirmacao de agendamento;
  - lembrete do dia;
  - lembrete com link de confirmacao/cancelamento;
  - verificacao de e-mail;
  - reset de senha.
- Fallback local para console/fake sem chamada externa.
- `NotificacaoLog` mantendo status `ENVIADO` ou `FALHOU`.
- Opcional: adicionar campos `provider` e `provider_message_id` em `NotificacaoLog`.

### Criterios de aceite

- [x] Todos os metodos publicos atuais de `NotificacaoService` continuam com a mesma assinatura.
- [x] A troca entre SMTP e Brevo acontece somente por `.env`, sem mudanca de codigo.
- [x] Templates HTML existentes continuam sendo renderizados.
- [x] Texto puro continua disponivel como fallback.
- [x] Falha de envio nao quebra criacao de agendamento, mantendo comportamento atual.
- [x] `NotificacaoLog` registra sucesso e falha para cada tentativa de envio ligada a agendamento.
- [x] Se `provider_message_id` for implementado, ele e persistido no sucesso.
- [x] Nenhum novo fluxo de campanha, lista ou contato e criado.

### Testes

- [ ] Unitarios para cada metodo publico de `NotificacaoService`, com provider mockado.
- [x] Teste de falha: provider retorna erro e cria `NotificacaoLog(status="FALHOU")`.
- [x] Teste de sucesso: provider retorna `message_id` e cria `NotificacaoLog(status="ENVIADO")`.
- [x] Teste de regressao coberto indiretamente: metodos de agendamento nao propagam falha do provider.

## Fase 4: Comandos, fluxos e templates

### Entregaveis

- `enviar_lembretes` funcionando com provider Brevo sem mudanca na interface do comando.
- Fluxo de confirmacao por link preservado.
- Reset de senha e verificacao de e-mail enviados via API quando provider ativo.
- Documentacao operacional para testar envio em desenvolvimento e producao.

### Criterios de aceite

- [x] `python manage.py enviar_lembretes` usa Brevo quando `EMAIL_PROVIDER=brevo`.
- [x] Agendamentos `AGENDADO` continuam recebendo lembretes conforme `LEMBRETE_DIAS_ANTECEDENCIA`.
- [x] Links gerados continuam usando `SITE_URL`.
- [x] Reset de senha gera link absoluto valido.
- [x] E-mail de verificacao continua usando codigo de 6 digitos com expiracao existente.

### Testes

- [ ] Teste do management command com provider mockado.
- [ ] Teste de `enviar_lembretes` verificando quantidade de chamadas ao provider.
- [x] Smoke local de reset de senha com provider Brevo.
- [ ] Teste automatizado de reset de senha com mock, validando que o link aparece no HTML/texto.
- [ ] Teste de verificacao de e-mail com mock, validando codigo no corpo.

## Fase 5: Observabilidade, seguranca e deploy

### Entregaveis

- Logs estruturados o suficiente para diagnosticar falhas por destinatario e tipo de notificacao.
- Mascaramento de erros que possam conter credenciais.
- README ou `ARCHITECTURE.md` atualizado com configuracao Brevo.
- Instrucoes para configurar variaveis no Render.
- Checklist manual de smoke test em ambiente real.

### Criterios de aceite

- [x] Logs mostram tipo da notificacao, destinatario e id do agendamento quando aplicavel.
- [x] Logs nao mostram `API_KEY_BREVO`.
- [ ] Render tem `API_KEY_BREVO`, `EMAIL_PROVIDER=brevo`, `BREVO_SENDER_NAME` e `BREVO_SENDER_EMAIL`.
- [ ] Um envio real de teste e recebido no destinatario esperado.
- [ ] Falha real de API aparece em `NotificacaoLog` e nos logs da aplicacao.

### Testes

- [ ] Smoke manual: criar agendamento e conferir e-mail recebido.
- [x] Smoke local: acionar "esqueci minha senha" com Brevo configurado.
- [ ] Smoke em producao: acionar "esqueci minha senha" e conferir link recebido.
- [ ] Smoke manual: executar `python manage.py enviar_lembretes` com um agendamento de teste.
- [ ] Verificacao manual no painel Brevo: confirmar evento de envio/entrega quando disponivel.

## Riscos e decisoes

| Risco | Mitigacao |
|---|---|
| Usar API de campanhas para mensagens transacionais | Nao implementar campanhas; usar somente `TransactionalEmailsApi.send_transac_email` |
| Chave Brevo vazando em log ou commit | Nunca ler/imprimir valor do `.env`; mascarar erros; manter apenas placeholder em `.env.example` |
| Testes chamando API real | Mock obrigatorio do SDK em testes automatizados |
| Sender nao validado na Brevo | Documentar requisito e testar em producao antes de ativar |
| Divergencia entre SMTP antigo e API nova | Manter assinatura de `NotificacaoService` e cobrir fluxos existentes com testes |

## Fora de escopo

- Criar editor visual de campanhas.
- Gerenciar listas de contatos da Brevo.
- Sincronizar clientes da base local para listas Brevo.
- Implementar webhooks de entrega, abertura, clique ou bounce.
- Trocar os templates HTML existentes por novo design.
- Adicionar qualquer novo tipo de comunicacao por e-mail alem dos fluxos ja existentes.

## Checklist final da feature

- [x] Requirements atualizados.
- [x] Settings e `.env.example` atualizados.
- [x] Provider Brevo implementado.
- [x] `NotificacaoService` integrado ao provider.
- [x] Testes unitarios cobrindo sucesso e falha.
- [ ] Management command testado com mock.
- [x] Smoke local de reset de senha executado em ambiente controlado.
- [ ] Smoke real completo executado em producao/Render.
- [x] README/arquitetura atualizados.
