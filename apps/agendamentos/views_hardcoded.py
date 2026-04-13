"""Hardcoded availability - apenas segunda e terça, sem banco de dados"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def hardcoded_availability(request):
    """Hardcoded availability - apenas segunda e terça"""
    
    # Dados mockados - apenas segunda e terça
    hoje = datetime.now().date()
    
    # Encontrar próxima segunda
    dias_ate_segunda = (0 - hoje.weekday() + 7) % 7
    if dias_ate_segunda == 0:
        dias_ate_segunda = 7  # Pular para próxima semana se hoje for segunda
    
    # Encontrar próxima terça  
    dias_ate_terca = (1 - hoje.weekday() + 7) % 7
    if dias_ate_terca == 0:
        dias_ate_terca = 7  # Pular para próxima semana se hoje for terça
    
    segunda = hoje + timedelta(days=dias_ate_segunda)
    terca = hoje + timedelta(days=dias_ate_terca)
    
    # Gerar horários para segunda e terça
    horarios_segunda = []
    horarios_terca = []
    
    # Horários das 09:00 às 18:00, pulando almoço
    for hora in range(9, 18):
        if hora == 12:  # Pular almoço
            continue
        
        # Adicionar :00
        horarios_segunda.append(f"{hora:02d}:00")
        horarios_terca.append(f"{hora:02d}:00")
        
        # Adicionar :30 (exceto última hora)
        if hora < 17:
            horarios_segunda.append(f"{hora:02d}:30")
            horarios_terca.append(f"{hora:02d}:30")
    
    results = [
        {
            "date": segunda.isoformat(),
            "weekday": "Segunda-feira",
            "slots": horarios_segunda
        },
        {
            "date": terca.isoformat(),
            "weekday": "Terça-feira", 
            "slots": horarios_terca
        }
    ]
    
    return JsonResponse({
        "results": results,
        "has_next": False,
        "has_previous": False,
        "current_page": 1
    })
