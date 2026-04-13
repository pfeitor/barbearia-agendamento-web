# Script para verificar dados no banco
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.profissionais.models import Profissional, ProfessionalSchedule
from datetime import datetime

print("=== VERIFICAÇÃO DIRETA DO BANCO ===")

print("\n1. Profissionais:")
profissionais = Profissional.objects.all()
for prof in profissionais:
    print(f"  ID {prof.id}: {prof.nome} (Ativo: {prof.ativo})")

print("\n2. Schedules no banco:")
schedules = ProfessionalSchedule.objects.all()
for schedule in schedules:
    print(f"\n  Schedule ID {schedule.id}:")
    print(f"    Profissional: {schedule.profissional.nome} (ID: {schedule.profissional.id})")
    print(f"    Weekday (bruto): {schedule.weekday}")
    print(f"    Weekday label: {schedule.Weekday(schedule.weekday).label}")
    print(f"    Start time: {schedule.start_time}")
    print(f"    End time: {schedule.end_time}")
    print(f"    Lunch start: {schedule.lunch_start}")
    print(f"    Lunch end: {schedule.lunch_end}")
    print(f"    Is day off: {schedule.is_day_off}")

print("\n3. Conceito Python vs Django:")
print("   Python weekday(): 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo")
print("   Django choices: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo")

hoje = datetime.now().date()
print(f"\n4. Hoje: {hoje} (weekday: {hoje.weekday()} - {['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'][hoje.weekday()]})")

print("\n5. Próximos 7 dias com schedules:")
for i in range(7):
    data = hoje + datetime.timedelta(days=i)
    weekday = data.weekday()
    
    schedule_dia = schedules.filter(weekday=weekday).first()
    
    print(f"  Dia {i}: {data.strftime('%Y-%m-%d')} (weekday {weekday})")
    print(f"    Python: {['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'][weekday]}")
    print(f"    Tem schedule: {'SIM' if schedule_dia else 'NÃO'}")
    if schedule_dia:
        print(f"    Schedule weekday: {schedule_dia.weekday}")
        print(f"    Schedule label: {schedule_dia.Weekday(schedule_dia.weekday).label}")

print("\n6. Teste direto da API Hardcoded:")
# Simular o que a API hardcoded faz
dias_com_schedule = [0, 1]  # Segunda e Terça
for weekday in dias_com_schedule:
    dias_para_frente = (weekday - hoje.weekday() + 7) % 7
    if dias_para_frente == 0:
        dias_para_frente = 7
    
    data = hoje + datetime.timedelta(days=dias_para_frente)
    print(f"  Weekday {weekday} -> Data {data} ({['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'][weekday]})")
