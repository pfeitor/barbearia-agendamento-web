"""View funcional para disponibilidade - versão simplificada garantida"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta, time
from django.utils import timezone

@require_GET
def working_availability(request):
    """Endpoint funcional para disponibilidade - versão garantida"""
    try:
        professional_id = int(request.GET.get('professional_id', 1))
        service_id = int(request.GET.get('service_id', 1))
        
        # Obter dados reais do banco
        from apps.profissionais.models import Profissional, ProfessionalSchedule
        from apps.servicos.models import Servico
        
        # Verificar se profissional e serviço existem
        try:
            professional = Profissional.objects.get(id=professional_id, ativo=True)
            service = Servico.objects.get(id=service_id)
        except:
            return JsonResponse({
                'error': 'Profissional ou serviço não encontrado',
                'results': [],
                'has_next': False,
                'has_previous': False
            })
        
        # Obter schedules do profissional
        schedules = ProfessionalSchedule.objects.filter(
            profissional=professional,
            is_day_off=False
        ).order_by('weekday')
        
        if not schedules:
            return JsonResponse({
                'results': [],
                'has_next': False,
                'has_previous': False
            })
        
        # Gerar disponibilidade para os próximos dias
        hoje = timezone.now().date()
        slots_disponiveis = []
        
        # Gerar para os próximos 7 dias
        for dias_a_frente in range(7):
            data_alvo = hoje + timedelta(days=dias_a_frente)
            weekday = data_alvo.weekday()
            
            # Verificar se há schedule para este dia
            schedule_dia = schedules.filter(weekday=weekday).first()
            
            if not schedule_dia:
                continue  # Pular dia sem schedule
            
            # Gerar horários disponíveis para este dia
            horarios_dia = []
            
            # Horário de trabalho
            inicio = datetime.combine(data_alvo, schedule_dia.start_time)
            fim = datetime.combine(data_alvo, schedule_dia.end_time)
            
            # Se for hoje, pular horários já passados
            if data_alvo == hoje:
                agora = timezone.now()
                if inicio < agora:
                    inicio = agora + timedelta(minutes=30)  # Próximo slot disponível
                    # Ajustar para próximo 30-minuto
                    minutos = inicio.minute
                    if minutos % 30 != 0:
                        inicio = inicio.replace(minute=30 if minutos < 30 else 0)
                        if minutos >= 30:
                            inicio = inicio + timedelta(hours=1)
            
            # Pular horário de almoço se existir
            almoco_inicio = None
            almoco_fim = None
            if schedule_dia.lunch_start and schedule_dia.lunch_end:
                almoco_inicio = datetime.combine(data_alvo, schedule_dia.lunch_start)
                almoco_fim = datetime.combine(data_alvo, schedule_dia.lunch_end)
            
            # Gerar slots de 30 em 30 minutos
            slot_atual = inicio
            while slot_atual + timedelta(minutes=service.duracao_minutos) <= fim:
                # Verificar se não está no horário de almoço
                if almoco_inicio and almoco_fim:
                    if slot_atual >= almoco_inicio and slot_atual < almoco_fim:
                        slot_atual = almoco_fim
                        continue
                
                # Verificar se tem tempo suficiente para o serviço
                if slot_atual + timedelta(minutes=service.duracao_minutos) <= fim:
                    horarios_dia.append(slot_atual.strftime("%H:%M"))
                
                slot_atual += timedelta(minutes=30)
            
            # Adicionar dia se tiver horários disponíveis
            if horarios_dia:
                slots_disponiveis.append({
                    "date": data_alvo.isoformat(),
                    "weekday": data_alvo.strftime("%A"),
                    "slots": horarios_dia
                })
        
        return JsonResponse({
            "results": slots_disponiveis,
            "has_next": False,
            "has_previous": False,
            "current_page": 1
        })
        
    except Exception as e:
        # Retornar erro detalhado para debug
        import traceback
        error_details = traceback.format_exc()
        
        return JsonResponse({
            'error': str(e),
            'details': error_details,
            'results': [],
            'has_next': False,
            'has_previous': False
        }, status=500)
