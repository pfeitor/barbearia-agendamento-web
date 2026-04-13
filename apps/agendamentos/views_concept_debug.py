"""Debug endpoint para verificar conceito de weekdays"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def debug_concept(request):
    """Debug para verificar conceito de weekdays"""
    
    try:
        from apps.profissionais.models import ProfessionalSchedule
        
        hoje = datetime.now().date()
        
        # Conceito Python
        dias_python = {
            0: "Segunda-feira",
            1: "Terça-feira", 
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo"
        }
        
        debug_info = {
            "hoje": {
                "date": hoje.isoformat(),
                "weekday": hoje.weekday(),
                "weekday_name": dias_python[hoje.weekday()],
                "strftime_A": hoje.strftime("%A")
            },
            "conceito_python": dias_python,
            "conceito_django": dict(ProfessionalSchedule.Weekday.choices),
            "schedules": []
        }
        
        # Schedules no banco
        schedules = ProfessionalSchedule.objects.all()
        for schedule in schedules:
            debug_info["schedules"].append({
                "id": schedule.id,
                "profissional": schedule.profissional.nome,
                "weekday_banco": schedule.weekday,
                "weekday_label": schedule.Weekday(schedule.weekday).label,
                "start_time": str(schedule.start_time),
                "end_time": str(schedule.end_time),
                "is_day_off": schedule.is_day_off
            })
        
        # Verificar próximos dias
        debug_info["proximos_dias"] = []
        for i in range(7):
            data = hoje + timedelta(days=i)
            weekday = data.weekday()
            
            schedule_dia = schedules.filter(weekday=weekday).first()
            
            debug_info["proximos_dias"].append({
                "date": data.isoformat(),
                "weekday": weekday,
                "python_name": dias_python[weekday],
                "strftime_A": data.strftime("%A"),
                "tem_schedule": schedule_dia is not None,
                "schedule_info": {
                    "weekday_banco": schedule_dia.weekday,
                    "weekday_label": schedule_dia.Weekday(schedule_dia.weekday).label
                } if schedule_dia else None
            })
        
        return JsonResponse(debug_info)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': str(e.__class__.__name__)
        }, status=500)
