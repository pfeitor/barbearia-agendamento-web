# Guia de Testes - Sistema de Autenticação Dual

## Dados de Teste Criados

### Administrador
- **Email**: admin@barbearia.com
- **Senha**: admin123
- **Acesso**: Total ao sistema

### Cliente
- **Nome**: João Teste
- **Telefone**: 11999999999
- **Email**: joao@teste.com

## Fluxos para Testar

### 1. Acesso Inicial (UX Prioritária Cliente)

**Passos:**
1. Acesse: `http://127.0.0.1:8000`
2. **Resultado esperado**: Redireciona automaticamente para `/login-cliente/`
3. Verifique se o login do cliente é o formulário principal
4. Confirme que o link "Acesso administrativo" aparece discretamente

### 2. Login Cliente - Telefone Existente

**Passos:**
1. Em `/login-cliente/`, digite: `11999999999`
2. Clique em "Entrar"
3. **Resultado esperado**: 
   - Mensagem de boas-vindas
   - Redirecionamento para dashboard do cliente
   - Menu mostra opções: "Início", "Novo Agendamento", "Meus Agendamentos", "Meus Dados"

### 3. Login Cliente - Telefone Inexistente

**Passos:**
1. Em `/login-cliente/`, digite: `11111111111`
2. Clique em "Entrar"
3. **Resultado esperado**:
   - Mensagem informativa sobre cadastro
   - Redirecionamento para formulário de cadastro
   - Campo telefone pré-preenchido

### 4. Cadastro Automático de Cliente

**Passos:**
1. No formulário de cadastro, preencha todos os campos
2. Mantenha o telefone `11111111111`
3. **Resultado esperado**:
   - Cliente criado
   - Login automático
   - Dashboard do cliente exibido

### 5. Login Administrativo

**Passos:**
1. No login do cliente, clique em "Acesso administrativo"
2. Digite email: `admin@barbearia.com`
3. Digite senha: `admin123`
4. **Resultado esperado**:
   - Dashboard administrativo
   - Menu completo: "Painel", "Clientes", "Profissionais", "Serviços", "Agendamentos", "Django Admin"

### 6. Testes de Segurança - Cliente

**Acesso Negado a URLs Administrativas:**
1. Logue como cliente (telefone: 11999999999)
2. Tente acessar diretamente: `http://127.0.0.1:8000/painel/`
3. **Resultado esperado**: Erro 403 ou redirecionamento

**Acesso Negado a Dados de Terceiros:**
1. Logue como cliente
2. Tente acessar: `http://127.0.0.1:8000/clientes/`
3. **Resultado esperado**: Erro 403

**Isolamento de Agendamentos:**
1. Logue como cliente
2. Acesse: "Meus Agendamentos"
3. **Resultado esperado**: Apenas agendamentos do cliente João Teste

### 7. Testes de Segurança - Administrador

**Acesso Total:**
1. Logue como administrador
2. Acesse todas as URLs administrativas
3. **Resultado esperado**: Acesso liberado a todos os recursos

**Visualização Completa:**
1. Acesse lista de agendamentos
2. **Resultado esperado**: Todos os agendamentos visíveis

## Checklist de Validação

### UX e Navegação
- [ ] Página inicial mostra login cliente prioritário
- [ ] Link admin aparece discretamente
- [ ] Redirecionamentos funcionam corretamente
- [ ] Menus mudam conforme perfil logado

### Autenticação
- [ ] Cliente loga com telefone existente
- [ ] Cliente novo é redirecionado para cadastro
- [ ] Cadastro realiza login automático
- [ ] Admin loga com email e senha
- [ ] Logout funciona para ambos perfis

### Segurança
- [ ] Cliente não acessa URLs administrativas
- [ ] Cliente não vê dados de outros clientes
- [ ] Querysets filtrados por usuário
- [ ] Erro 403 exibido adequadamente

### Funcionalidades
- [ ] Dashboard cliente mostra apenas seus dados
- [ ] Dashboard admin mostra estatísticas completas
- [ ] Links de navegação funcionam
- [ ] Formulários processam corretamente

## URLs Importantes

### Fluxo Cliente
- `http://127.0.0.1:8000/` - Redireciona para login cliente
- `http://127.0.0.1:8000/login-cliente/` - Login do cliente
- `http://127.0.0.1:8000/logout-cliente/` - Logout do cliente
- `http://127.0.0.1:8000/agendamentos/meus-agendamentos/` - Agendamentos do cliente

### Fluxo Administrativo
- `http://127.0.0.1:8000/login-admin/` - Login do admin
- `http://127.0.0.1:8000/painel/` - Dashboard admin
- `http://127.0.0.1:8000/logout-admin/` - Logout do admin

### URLs Administrativas
- `http://127.0.0.1:8000/clientes/` - CRUD de clientes
- `http://127.0.0.1:8000/agendamentos/` - CRUD de agendamentos

## Troubleshooting

### Se o servidor não iniciar:
```bash
python manage.py runserver 0.0.0.0:8000
```

### Se houver erro de importação:
```bash
python manage.py check
```

### Se os dados de teste não existirem:
```bash
python manage.py shell
# E executar os comandos do arquivo validate_setup.py
```

## Próximos Passos

Após validar todos os fluxos:
1. Teste no ambiente de desenvolvimento
2. Faça o deploy para Render
3. Teste em produção
4. Configure backup dos dados
5. Monitore os logs de acesso

## Contato

Se encontrar algum problema durante os testes:
1. Verifique os logs do servidor
2. Confirme se todos os arquivos foram criados
3. Verifique as configurações em settings/base.py
4. Teste individualmente cada componente
