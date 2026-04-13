# Teste simples para debug
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

print("Iniciando teste...")

try:
    from apps.profissionais.models import Profissional, ProfessionalSchedule
    print("Importou Profissional e ProfessionalSchedule")
except Exception as e:
    print(f"Erro ao importar modelos: {e}")

try:
    from apps.servicos.models import Servico
    print("Importou Servico")
except Exception as e:
    print(f"Erro ao importar Servico: {e}")

try:
    from apps.agendamentos.services import AvailabilityService
    print("Importou AvailabilityService")
except Exception as e:
    print(f"Erro ao importar AvailabilityService: {e}")

# Testar se os modelos existem
try:
    prof_count = Profissional.objects.count()
    print(f"Profissionais no banco: {prof_count}")
except Exception as e:
    print(f"Erro ao contar profissionais: {e}")

try:
    schedule_count = ProfessionalSchedule.objects.count()
    print(f"Schedules no banco: {schedule_count}")
except Exception as e:
    print(f"Erro ao contar schedules: {e}")

try:
    service_count = Servico.objects.count()
    print(f"Serviços no banco: {service_count}")
except Exception as e:
    print(f"Erro ao contar serviços: {e}")

print("Teste concluído!")
