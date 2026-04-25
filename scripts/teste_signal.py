"""Cria um agendamento de teste para disparar o signal de notificacao."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django; django.setup()

from django.utils import timezone
from datetime import timedelta
from apps.clientes.models import Cliente
from apps.profissionais.models import Profissional
from apps.servicos.models import Servico
from apps.agendamentos.models import Agendamento

# Busca o primeiro cliente, profissional e servico disponiveis
cliente = Cliente.objects.first()
profissional = Profissional.objects.filter(ativo=True).first()
servico = Servico.objects.first()

if not all([cliente, profissional, servico]):
    print("ERRO: Nao ha cliente, profissional ou servico cadastrado.")
    sys.exit(1)

# Agendamento para amanha as 10h
data_hora = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)

print(f"Criando agendamento de teste...")
print(f"  Cliente:      {cliente.nome} ({cliente.email})")
print(f"  Profissional: {profissional.nome}")
print(f"  Servico:      {servico.nome}")
print(f"  Data/Hora:    {timezone.localtime(data_hora):%d/%m/%Y as %H:%M}")
print()

agendamento = Agendamento.objects.create(
    cliente=cliente,
    profissional=profissional,
    servico=servico,
    data_hora_inicio=data_hora,
    status=Agendamento.Status.AGENDADO,
)

print(f"Agendamento #{agendamento.pk} criado.")
print("Signal deve ter disparado o envio do e-mail...")
print()

# Verificar log
from apps.notificacoes.models import NotificacaoLog
log = NotificacaoLog.objects.filter(agendamento=agendamento).first()
if log:
    print(f"[LOG ENCONTRADO]")
    print(f"  Status:      {log.status}")
    print(f"  Tipo:        {log.tipo}")
    print(f"  Destinatario: {log.destinatario}")
    if log.erro:
        print(f"  ERRO: {log.erro}")
else:
    print("[ATENCAO] Nenhum log encontrado - signal pode nao ter disparado.")
