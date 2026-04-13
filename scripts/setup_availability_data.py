#!/usr/bin/env python
"""
Setup script for availability system example data.

This script creates sample professional schedules and demonstrates the availability system.
Run with: python manage.py shell < scripts/setup_availability_data.py
"""

from datetime import time
from apps.profissionais.models import Profissional, ProfessionalSchedule
from apps.clientes.models import Cliente
from apps.servicos.models import Servico
from apps.agendamentos.models import Agendamento
from django.utils import timezone


def create_sample_professionals():
    """Create sample professionals with schedules."""
    
    professionals_data = [
        {
            "nome": "João Silva",
            "schedules": {
                0: {"start": "09:00", "end": "18:00", "lunch_start": "12:00", "lunch_end": "13:00"},  # Monday
                1: {"start": "09:00", "end": "18:00", "lunch_start": "12:00", "lunch_end": "13:00"},  # Tuesday
                2: {"start": "09:00", "end": "18:00", "lunch_start": "12:00", "lunch_end": "13:00"},  # Wednesday
                3: {"start": "09:00", "end": "18:00", "lunch_start": "12:00", "lunch_end": "13:00"},  # Thursday
                4: {"start": "09:00", "end": "17:00", "lunch_start": "12:00", "lunch_end": "13:00"},  # Friday
                5: {"start": "08:00", "end": "14:00", "lunch_start": None, "lunch_end": None},      # Saturday
                6: None,  # Sunday off
            }
        },
        {
            "nome": "Maria Santos",
            "schedules": {
                0: {"start": "08:00", "end": "16:00", "lunch_start": "11:30", "lunch_end": "12:30"},  # Monday
                1: {"start": "08:00", "end": "16:00", "lunch_start": "11:30", "lunch_end": "12:30"},  # Tuesday
                2: None,  # Wednesday off
                3: {"start": "08:00", "end": "16:00", "lunch_start": "11:30", "lunch_end": "12:30"},  # Thursday
                4: {"start": "08:00", "end": "16:00", "lunch_start": "11:30", "lunch_end": "12:30"},  # Friday
                5: {"start": "07:00", "end": "12:00", "lunch_start": None, "lunch_end": None},       # Saturday
                6: None,  # Sunday off
            }
        },
        {
            "nome": "Pedro Costa",
            "schedules": {
                1: {"start": "14:00", "end": "22:00", "lunch_start": "18:00", "lunch_end": "19:00"},  # Tuesday
                2: {"start": "14:00", "end": "22:00", "lunch_start": "18:00", "lunch_end": "19:00"},  # Wednesday
                3: {"start": "14:00", "end": "22:00", "lunch_start": "18:00", "lunch_end": "19:00"},  # Thursday
                4: {"start": "14:00", "end": "22:00", "lunch_start": "18:00", "lunch_end": "19:00"},  # Friday
                5: {"start": "10:00", "end": "18:00", "lunch_start": "14:00", "lunch_end": "15:00"},  # Saturday
                6: {"start": "10:00", "end": "18:00", "lunch_start": "14:00", "lunch_end": "15:00"},  # Sunday
                0: None,  # Monday off
            }
        }
    ]
    
    for prof_data in professionals_data:
        # Create professional
        professional, created = Profissional.objects.get_or_create(
            nome=prof_data["nome"],
            defaults={"ativo": True}
        )
        
        if created:
            print(f"Created professional: {professional.nome}")
        
        # Clear existing schedules
        professional.schedules.all().delete()
        
        # Create schedules
        for weekday, schedule_data in prof_data["schedules"].items():
            if schedule_data is None:
                # Day off
                ProfessionalSchedule.objects.create(
                    profissional=professional,
                    weekday=weekday,
                    is_day_off=True
                )
                print(f"  - Day {weekday}: OFF")
            else:
                # Working day
                ProfessionalSchedule.objects.create(
                    profissional=professional,
                    weekday=weekday,
                    start_time=time.fromisoformat(schedule_data["start"]),
                    end_time=time.fromisoformat(schedule_data["end"]),
                    lunch_start=time.fromisoformat(schedule_data["lunch_start"]) if schedule_data["lunch_start"] else None,
                    lunch_end=time.fromisoformat(schedule_data["lunch_end"]) if schedule_data["lunch_end"] else None,
                    is_day_off=False
                )
                lunch_info = f" (lunch: {schedule_data['lunch_start']}-{schedule_data['lunch_end']})" if schedule_data["lunch_start"] else ""
                print(f"  - Day {weekday}: {schedule_data['start']}-{schedule_data['end']}{lunch_info}")


def create_sample_services():
    """Create sample services."""
    
    services_data = [
        {"nome": "Corte de Cabelo Masculino", "duracao_minutos": 30, "preco": 50.00},
        {"nome": "Corte de Cabelo Feminino", "duracao_minutos": 45, "preco": 80.00},
        {"nome": "Barba", "duracao_minutos": 20, "preco": 30.00},
        {"nome": "Corte + Barba", "duracao_minutos": 50, "preco": 70.00},
        {"nome": "Hidratação", "duracao_minutos": 40, "preco": 60.00},
        {"nome": "Progressiva", "duracao_minutos": 120, "preco": 150.00},
        {"nome": "Coloração", "duracao_minutos": 90, "preco": 120.00},
        {"nome": "Selagem", "duracao_minutos": 100, "preco": 130.00},
    ]
    
    for service_data in services_data:
        service, created = Servico.objects.get_or_create(
            nome=service_data["nome"],
            defaults=service_data
        )
        
        if created:
            print(f"Created service: {service.nome} ({service.duracao_minutos}min, R${service.preco})")


def create_sample_clients():
    """Create sample clients."""
    
    clients_data = [
        {"nome": "Carlos Oliveira", "email": "carlos@email.com", "telefone": "11987654321"},
        {"nome": "Ana Silva", "email": "ana@email.com", "telefone": "11987654322"},
        {"nome": "Roberto Santos", "email": "roberto@email.com", "telefone": "11987654323"},
        {"nome": "Fernanda Costa", "email": "fernanda@email.com", "telefone": "11987654324"},
        {"nome": "Lucas Pereira", "email": "lucas@email.com", "telefone": "11987654325"},
    ]
    
    for client_data in clients_data:
        client, created = Cliente.objects.get_or_create(
            email=client_data["email"],
            defaults=client_data
        )
        
        if created:
            print(f"Created client: {client.nome}")


def create_sample_appointments():
    """Create some sample appointments to test availability."""
    
    from datetime import datetime, timedelta
    
    # Get some sample data
    joao = Profissional.objects.get(nome="João Silva")
    maria = Profissional.objects.get(nome="Maria Santos")
    
    corte = Servico.objects.get(nome="Corte de Cabelo Masculino")
    barba = Servico.objects.get(nome="Barba")
    corte_barba = Servico.objects.get(nome="Corte + Barba")
    
    carlos = Cliente.objects.get(nome="Carlos Oliveira")
    ana = Cliente.objects.get(nome="Ana Silva")
    
    # Create some appointments for today and tomorrow
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    appointments = [
        # Today's appointments for João
        {
            "datetime": today + timedelta(hours=9, minutes=0),
            "professional": joao,
            "service": corte,
            "client": carlos,
        },
        {
            "datetime": today + timedelta(hours=10, minutes=30),
            "professional": joao,
            "service": barba,
            "client": ana,
        },
        {
            "datetime": today + timedelta(hours=14, minutes=0),
            "professional": joao,
            "service": corte_barba,
            "client": carlos,
        },
        
        # Tomorrow's appointments for Maria
        {
            "datetime": tomorrow + timedelta(hours=8, minutes=30),
            "professional": maria,
            "service": corte,
            "client": ana,
        },
        {
            "datetime": tomorrow + timedelta(hours=13, minutes=0),
            "professional": maria,
            "service": barba,
            "client": carlos,
        },
    ]
    
    for appt_data in appointments:
        appointment, created = Agendamento.objects.get_or_create(
            data_hora_inicio=appt_data["datetime"],
            profissional=appt_data["professional"],
            servico=appt_data["service"],
            cliente=appt_data["client"],
            defaults={
                "status": Agendamento.Status.CONFIRMADO,
                "confirmado_whatsapp": True,
            }
        )
        
        if created:
            print(f"Created appointment: {appointment.cliente.nome} - {appointment.servico.nome} - {appointment.data_hora_inicio}")


def main():
    """Main setup function."""
    print("=== Setting up Availability System Sample Data ===\n")
    
    print("1. Creating professionals and schedules...")
    create_sample_professionals()
    
    print("\n2. Creating services...")
    create_sample_services()
    
    print("\n3. Creating clients...")
    create_sample_clients()
    
    print("\n4. Creating sample appointments...")
    create_sample_appointments()
    
    print("\n=== Setup Complete! ===")
    print("\nYou can now test the availability system:")
    print("1. Run: python manage.py runserver")
    print("2. Visit: http://127.0.0.1:8000/agendamentos/novo/")
    print("3. API endpoint: http://127.0.0.1:8000/agendamentos/availability/?professional_id=1&service_id=1")
    
    print("\nProfessional IDs and Service IDs:")
    for prof in Profissional.objects.all():
        print(f"  {prof.nome}: ID {prof.id}")
    
    for service in Servico.objects.all():
        print(f"  {service.nome}: ID {service.id}")


if __name__ == "__main__":
    main()
