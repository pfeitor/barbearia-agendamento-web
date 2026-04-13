"""API definitiva - apenas segunda e terça, sem banco, sem cache"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def definitiva_availability(request):
    """API definitiva - hardcoded para apenas segunda e terça"""
    
    # Dados fixos - apenas segunda e terça
    hoje = datetime.now().date()
    
    # Encontrar próxima segunda e terça
    dias_ate_segunda = (0 - hoje.weekday() + 7) % 7
    if dias_ate_segunda == 0:
        dias_ate_segunda = 7
    
    dias_ate_terca = (1 - hoje.weekday() + 7) % 7
    if dias_ate_terca == 0:
        dias_ate_terca = 7
    
    segunda = hoje + timedelta(days=dias_ate_segunda)
    terca = hoje + timedelta(days=dias_ate_terca)
    
    # Gerar horários fixos
    horarios = []
    for hora in range(9, 18):
        if hora == 12:  # Pular almoço
            continue
        horarios.append(f"{hora:02d}:00")
        if hora < 17:
            horarios.append(f"{hora:02d}:30")
    
    results = [
        {
            "date": segunda.isoformat(),
            "weekday": "Segunda-feira",
            "slots": horarios
        },
        {
            "date": terca.isoformat(),
            "weekday": "Terça-feira",
            "slots": horarios
        }
    ]
    
    return JsonResponse({
        "results": results,
        "has_next": False,
        "has_previous": False,
        "current_page": 1
    })
