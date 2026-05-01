# Feature 01: Autenticação por E-mail/Senha + Recuperação + Conclusão de Agendamento

## 🎯 Contexto & Objetivo
Substituir a autenticação atual por telefone por um fluxo baseado em `Django User`, adicionando verificação de e-mail, reset de senha seguro e status "CONCLUÍDO" para admins. Manter 100% de compatibilidade com agendamentos e dados existentes.

## 📐 Escopo Técnico
### Models (`clientes/models.py`)
- `ClienteUser(AbstractUser)`: `email` como `USERNAME_FIELD` (único), `is_active=False` por padrão.
- `VerificacaoEmail(cliente_user: FK, code: Char(6), expires_at: DateTime, is_used: Boolean)`
- Manter model `Cliente` atual. Criar `OneToOneField(cliente_user, on_delete=CASCADE, related_name='perfil')`.

### Views & URLs
- `/clientes/registrar/` → `ClienteRegisterView` (form e-mail/senha)
- `/clientes/verificar/` → `VerificarEmailView` (input código 6 dígitos)
- `/clientes/login/` & `/clientes/logout/`
- `/clientes/esqueci-senha/` → `PasswordResetRequestView`
- `/clientes/resetar-senha/<uidb64>/<token>/` → `PasswordResetConfirmView`
- `/agendamentos/<pk>/concluir/` → `AgendamentoConcluirView` (protegida por `AdminRequiredMixin`)

### Services (`clientes/services.py` & `notificacoes/services.py`)
- `AuthService.gerar_codigo_verificacao()`: salva código, expiração 15min, limite 3 envios/hora.
- `AuthService.enviar_email_verificacao()` & `enviar_email_reset()`: usa `notificacoes/services.py`.
- `AgendamentoService.concluir_agendamento()`: transiciona `AGENDADO/CONFIRMADO` → `CONCLUÍDO`, invalida cache via signal.

### Segurança & Validações
- Senha: mínimo 8 chars, 1 maiúscula, 1 número. Validação via `PasswordValidator`.
- Reset de senha: usa `django.contrib.auth.tokens.default_token_generator` (HMAC + timestamp). Expira em 1h.
- Formulário de nova senha: campos `nova_senha` e `confirmar_senha` com validação de igualdade explícita.
- Rate limit: 3 tentativas de reset/verificação por IP/e-mail a cada hora.

## 🔄 Fluxo de Dados
1. Cadastro → gera `ClienteUser(is_active=False)` → envia código → valida → `is_active=True` → login automático.
2. Esqueci senha → gera token → envia link → valida token → atualiza password → invalida token → redireciona login.
3. Admin conclui → atualiza status → dispara `agendamento_concluido` signal → invalida cache de disponibilidade → log.

## ✅ Critérios de Aceite
- [ ] Login por telefone desabilitado/removido sem quebrar URLs antigas (redirect 301 ou mensagem clara).
- [ ] Migração de dados: clientes existentes recebem `ClienteUser` com e-mail temporário ou são obrigados a revalidar.
- [ ] `ClienteRequiredMixin` adaptada para verificar `request.user.cliente` e `is_active`.
- [ ] Templates usam `base.html` existente. Mensagens de erro/sucesso via `django.contrib.messages`.
- [ ] `ARCHITECTURE.md` atualizado com novo fluxo de auth, models e rotas.

## ⚠️ Impacto na Arquitetura Atual
- Substitui `TelefoneBackend` por `ModelBackend` padrão do Django.
- Remove dependência de sessão por `cliente_id`.
- Adiciona dependência de `django.core.mail` configurada (já existente no projeto).
- Mantém `locmem` cache (5 min) e invalidação por signals.