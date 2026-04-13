"""View simplificada para testar disponibilidade"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta, time
from django.utils import timezone

@require_GET
def simple_availability(request):
    """Endpoint simplificado para disponibilidade"""
    try:
        professional_id = int(request.GET.get('professional_id', 1))
        service_id = int(request.GET.get('service_id', 1))
        
        # Dados mockados para teste
        hoje = timezone.now().date()
        
        # Gerar alguns slots para hoje e amanhã
        slots = []
        
        # Hoje - só se ainda não for muito tarde
        if timezone.now().hour < 17:
            for hour in range(9, 18):
                if hour != 12:  # Pular almoço
                    slots.append({
                        "date": hoje.isoformat(),
                        "weekday": hoje.strftime("%A"),
                        "slots": [f"{hour:02d}:00"]
                    })
                    break  # Só um slot por dia no exemplo
        
        # Amanhã
        amanha = hoje + timedelta(days=1)
        slots.append({
            "date": amanha.isoformat(),
            "weekday": amanha.strftime("%A"),
            "slots": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]
        })
        
        return JsonResponse({
            "results": slots,
            "has_next": True,
            "has_previous": False,
            "current_page": 1
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'results': [],
            'has_next': False,
            'has_previous': False
        }, status=500)
