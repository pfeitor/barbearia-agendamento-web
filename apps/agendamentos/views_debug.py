"""Views de debug para identificar problemas"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def debug_availability_test(request):
    """Endpoint de debug para testar disponibilidade"""
    try:
        # Testar importações
        from apps.profissionais.models import Profissional, ProfessionalSchedule
        from apps.servicos.models import Servico
        from apps.agendamentos.services import AvailabilityService
        
        # Coletar dados
        profissionais = list(Profissional.objects.values('id', 'nome', 'ativo'))
        schedules = list(ProfessionalSchedule.objects.values('profissional_id', 'weekday', 'start_time', 'end_time', 'is_day_off'))
        servicos = list(Servico.objects.values('id', 'nome', 'duracao_minutos'))
        
        return JsonResponse({
            'status': 'success',
            'imports': 'OK',
            'profissionais': profissionais,
            'schedules': schedules,
            'servicos': servicos,
            'total_profissionais': len(profissionais),
            'total_schedules': len(schedules),
            'total_servicos': len(servicos)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)

@require_GET
def debug_simple_test(request):
    """Teste simples sem dependências"""
    return JsonResponse({
        'status': 'working',
        'message': 'Django está funcionando',
        'get_params': dict(request.GET)
    })
