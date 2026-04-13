#!/usr/bin/env python
"""
Script para debug do sistema de disponibilidade
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

print("=== DEBUG DO SISTEMA DE DISPONIBILIDADE ===")

# 1. Verificar modelos
try:
    from apps.profissionais.models import Profissional, ProfessionalSchedule
    from apps.servicos.models import Servico
    from apps.agendamentos.services import AvailabilityService
    print("1. Importações: OK")
except ImportError as e:
    print(f"1. Erro de importação: {e}")
    exit()

# 2. Verificar dados no banco
print("\n2. Dados no banco:")
profissionais = Profissional.objects.all()
print(f"   Profissionais: {profissionais.count()}")
for p in profissionais:
    print(f"   - {p.nome} (ID: {p.id}, Ativo: {p.ativo})")

schedules = ProfessionalSchedule.objects.all()
print(f"   Schedules: {schedules.count()}")
for s in schedules:
    weekday_name = s.Weekday(s.weekday).label
    print(f"   - {s.profissional.nome} - {weekday_name}: {s.start_time}-{s.end_time} (Folga: {s.is_day_off})")

servicos = Servico.objects.all()
print(f"   Serviços: {servicos.count()}")
for s in servicos:
    print(f"   - {s.nome} (ID: {s.id}) - {s.duracao_minutos}min")

# 3. Testar availability
print("\n3. Teste de disponibilidade:")
if profissionais.exists() and servicos.exists():
    prof = profissionais.first()
    service = servicos.first()
    
    print(f"   Testando: {prof.nome} (ID: {prof.id}) + {service.nome} (ID: {service.id})")
    
    try:
        result = AvailabilityService.get_available_slots(prof.id, service.id, 1)
        print(f"   Resultado: {len(result.get('results', []))} dias disponíveis")
        if result.get('results'):
            for day in result['results'][:2]:  # Mostrar só 2 primeiros dias
                print(f"   - {day['date']}: {len(day['slots'])} slots")
        else:
            print("   Nenhum resultado")
    except Exception as e:
        print(f"   ERRO: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   Não há dados suficientes para testar")

# 4. Verificar URLs
print("\n4. URLs configuradas:")
try:
    from django.urls import reverse
    api_url = reverse('availability_api')
    print(f"   API URL: {api_url}")
except Exception as e:
    print(f"   Erro na URL: {e}")

print("\n=== FIM DO DEBUG ===")
