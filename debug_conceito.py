# Script para debug do conceito de weekdays
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from datetime import datetime, timedelta
from apps.profissionais.models import Profissional, ProfessionalSchedule

print("=== DEBUG DO CONCEITO DE WEEKDAYS ===")

hoje = datetime.now().date()
print(f"Hoje: {hoje} (weekday: {hoje.weekday()})")

# Conceito Python/Django
print("\nConceito Python/Django (weekday()):")
dias_python = {
    0: "Segunda-feira",
    1: "Terça-feira", 
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo"
}

for i in range(7):
    print(f"  {i} = {dias_python[i]}")

print("\nConceito Django Model (ProfessionalSchedule.Weekday):")
for choice in ProfessionalSchedule.Weekday.choices:
    print(f"  {choice[0]} = {choice[1]}")

print("\nSchedules no banco:")
schedules = ProfessionalSchedule.objects.all()
for schedule in schedules:
    print(f"\nSchedule ID {schedule.id}:")
    print(f"  Profissional: {schedule.profissional.nome}")
    print(f"  Weekday no banco: {schedule.weekday}")
    print(f"  Weekday label: {schedule.Weekday(schedule.weekday).label}")
    print(f"  Start time: {schedule.start_time}")
    print(f"  End time: {schedule.end_time}")

print("\nPróximos 7 dias (comparação):")
for i in range(7):
    data = hoje + timedelta(days=i)
    python_weekday = data.weekday()
    python_nome = dias_python[python_weekday]
    
    # Verificar se há schedule para este weekday
    schedule_dia = schedules.filter(weekday=python_weekday).first()
    
    print(f"  {data.strftime('%Y-%m-%d')} ({data.strftime('%A')})")
    print(f"    Python weekday: {python_weekday} ({python_nome})")
    print(f"    Tem schedule: {'SIM' if schedule_dia else 'NÃO'}")
    if schedule_dia:
        print(f"    Schedule weekday: {schedule_dia.weekday} ({schedule_dia.Weekday(schedule_dia.weekday).label})")
