"""Debug endpoint para weekdays"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def debug_weekdays(request):
    """Debug endpoint para verificar weekdays"""
    
    try:
        from apps.profissionais.models import ProfessionalSchedule
        
        hoje = datetime.now().date()
        
        # Dias da semana em português
        dias_semana = {
            0: "Segunda-feira",
            1: "Terça-feira", 
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo"
        }
        
        # Obter schedules
        schedules = ProfessionalSchedule.objects.all()
        
        debug_info = {
            "hoje": {
                "date": hoje.isoformat(),
                "weekday": hoje.weekday(),
                "weekday_name": dias_semana[hoje.weekday()],
                "strftime_A": hoje.strftime("%A")
            },
            "schedules": [],
            "proximos_7_dias": []
        }
        
        # Informações dos schedules
        for schedule in schedules:
            debug_info["schedules"].append({
                "profissional": schedule.profissional.nome,
                "weekday": schedule.weekday,
                "weekday_label": schedule.Weekday(schedule.weekday).label,
                "start_time": str(schedule.start_time),
                "end_time": str(schedule.end_time),
                "is_day_off": schedule.is_day_off
            })
        
        # Próximos 7 dias
        for i in range(7):
            data = hoje + timedelta(days=i)
            weekday = data.weekday()
            
            # Verificar se há schedule para este dia
            schedule_dia = schedules.filter(weekday=weekday, is_day_off=False).first()
            
            debug_info["proximos_7_dias"].append({
                "dias_frente": i,
                "date": data.isoformat(),
                "weekday": weekday,
                "weekday_name": dias_semana[weekday],
                "strftime_A": data.strftime("%A"),
                "tem_schedule": schedule_dia is not None,
                "schedule_info": {
                    "start_time": str(schedule_dia.start_time),
                    "end_time": str(schedule_dia.end_time)
                } if schedule_dia else None
            })
        
        return JsonResponse(debug_info)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'details': str(e.__class__.__name__)
        }, status=500)
