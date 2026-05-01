# [Versão X.X.X] - [Data]

## 🎉 O que há de novo

### ✨ Novas Funcionalidades
- [Descrever as principais funcionalidades adicionadas]

### 🐛 Correções de Bugs
- [Listar bugs corrigidos]

### 🔧 Melhorias
- [Listar melhorias de performance/usabilidade]

---

## 📋 Checklist de Deploy

### ✅ Pré-Deploy
- [ ] Testes executados localmente
- [ ] Variáveis de ambiente atualizadas
- [ ] DATABASE_URL verificada
- [ ] SECRET_KEY configurada
- [ ] Backup do banco (se necessário)

### ✅ Deploy
- [ ] Build concluído com sucesso
- [ ] Migrações aplicadas
- [ ] Static files coletados
- [ ] Serviço rodando

### ✅ Pós-Deploy
- [ ] Funcionalidades críticas testadas
- [ ] Sistema de e-mails funcionando
- [ ] Logs verificados
- [ ] Performance monitorada

---

## 🚀 Como Instalar/Atualizar

### Para Nova Instalação
```bash
git clone https://github.com/pfeitor/barbearia-agendamento-web.git
cd barbearia-agendamento-web
pip install -r requirements/prod.txt
# Configurar variáveis de ambiente
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Para Atualizar
```bash
git pull origin main
pip install -r requirements/prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## 🔗 Links Importantes

- [Aplicação em Produção](https://pi-barbearia.onrender.com)
- [Documentação](README.md)
- [Issues](https://github.com/pfeitor/barbearia-agendamento-web/issues)

---

## 📝 Notas da Versão

### Mudanças Técnicas
- [Listar mudanças técnicas relevantes]

### Dependências
- [Listar atualizações de dependências]

### Compatibilidade
- Python 3.8+
- Django 5.1+

---

## 👥 Contribuidores

- [@pfeitor](https://github.com/pfeitor) - Desenvolvimento principal

---

## 📄 Licença

Este projeto é de uso acadêmico / educacional.
