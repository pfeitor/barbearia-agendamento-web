"""View simples para verificar dados do banco em HTML"""

from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta

def banco_check_view(request):
    """View para verificar dados do banco"""
    
    from apps.profissionais.models import Profissional, ProfessionalSchedule
    
    hoje = datetime.now().date()
    
    # Obter dados
    profissionais = Profissional.objects.all()
    schedules = ProfessionalSchedule.objects.all()
    
    # Preparar dados para o template
    dados = {
        'hoje': hoje,
        'hoje_weekday': hoje.weekday(),
        'profissionais': profissionais,
        'schedules': [],
        'proximos_dias': []
    }
    
    # Preparar schedules com labels
    for schedule in schedules:
        dados['schedules'].append({
            'id': schedule.id,
            'profissional': schedule.profissional,
            'weekday': schedule.weekday,
            'weekday_label': schedule.Weekday(schedule.weekday).label,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'lunch_start': schedule.lunch_start,
            'lunch_end': schedule.lunch_end,
            'is_day_off': schedule.is_day_off
        })
    
    # Próximos 7 dias
    for i in range(7):
        data = hoje + timedelta(days=i)
        weekday = data.weekday()
        schedule_dia = schedules.filter(weekday=weekday).first()
        
        dados['proximos_dias'].append({
            'numero': i,
            'data': data,
            'weekday': weekday,
            'weekday_nome': ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][weekday],
            'tem_schedule': schedule_dia is not None,
            'schedule': schedule_dia
        })
    
    return render(request, 'agendamentos/banco_check.html', dados)
