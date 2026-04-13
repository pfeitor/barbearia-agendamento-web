# Script para debug dos weekdays
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from datetime import datetime, timedelta
from apps.profissionais.models import Profissional, ProfessionalSchedule

print("=== DEBUG DE WEEKDAYS ===")

hoje = datetime.now().date()
print(f"Hoje: {hoje} (weekday: {hoje.weekday()})")

print("\nDias da semana (Python):")
dias_semana = {
    0: "Segunda-feira",
    1: "Terça-feira", 
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo"
}

for i in range(7):
    data = hoje + timedelta(days=i)
    print(f"Dia +{i}: {data} ({data.strftime('%A')} - weekday: {data.weekday()}) - {dias_semana[data.weekday()]}")

print("\nSchedules no banco:")
schedules = ProfessionalSchedule.objects.all()
for schedule in schedules:
    weekday_name = schedule.Weekday(schedule.weekday).label
    print(f"  {schedule.profissional.nome} - Weekday {schedule.weekday} ({weekday_name}) - {schedule.start_time}-{schedule.end_time}")

print("\nPróximos 7 dias com schedules:")
for i in range(7):
    data = hoje + timedelta(days=i)
    weekday = data.weekday()
    
    # Verificar se há schedule para este dia
    schedule_dia = schedules.filter(weekday=weekday).first()
    
    if schedule_dia:
        print(f"  {data.strftime('%Y-%m-%d')} ({dias_semana[weekday]}) - TEM SCHEDULE")
    else:
        print(f"  {data.strftime('%Y-%m-%d')} ({dias_semana[weekday]}) - sem schedule")
