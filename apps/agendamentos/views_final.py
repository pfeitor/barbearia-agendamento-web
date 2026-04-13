"""Final availability version - no timezone issues"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta, time

@require_GET
def final_availability(request):
    """Final availability - sem problemas de timezone"""
    
    try:
        professional_id = int(request.GET.get('professional_id', 1))
        service_id = int(request.GET.get('service_id', 1))
        
        # Importar modelos
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
        
        # Obter schedules reais do profissional
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
        
        # Criar dicionário de schedules por weekday
        schedules_por_dia = {}
        for schedule in schedules:
            schedules_por_dia[schedule.weekday] = schedule
        
        hoje = datetime.now().date()
        agora_hora = datetime.now().hour
        agora_minuto = datetime.now().minute
        
        results = []
        
        # Gerar slots para os próximos 7 dias
        for i in range(7):
            data = hoje + timedelta(days=i)
            weekday = data.weekday()

            # Se for o dia de hoje e não houver schedule, pular
            if i == 0 and weekday not in schedules_por_dia:
                continue
            
            # Verificar se há schedule para este dia
            if weekday not in schedules_por_dia:
                continue  # Pular dia sem schedule
            
            schedule = schedules_por_dia[weekday]
            slots = []
            
            # Gerar horários baseados no schedule real
            hora_inicio = schedule.start_time.hour
            minuto_inicio = schedule.start_time.minute
            hora_fim = schedule.end_time.hour
            minuto_fim = schedule.end_time.minute
            
            # Se for hoje, pular horários já passados
            if data == hoje:
                if hora_inicio < agora_hora or (hora_inicio == agora_hora and minuto_inicio <= agora_minuto):
                    # Ajustar para próxima hora
                    hora_inicio = agora_hora + 1
                    minuto_inicio = 0
                    if hora_inicio >= hora_fim:
                        continue  # Não há mais horários hoje
            
            # Verificar horário de almoço
            tem_almoco = schedule.lunch_start and schedule.lunch_end
            almoco_inicio_hora = schedule.lunch_start.hour if tem_almoco else None
            almoco_inicio_minuto = schedule.lunch_start.minute if tem_almoco else None
            almoco_fim_hora = schedule.lunch_end.hour if tem_almoco else None
            almoco_fim_minuto = schedule.lunch_end.minute if tem_almoco else None
            
            # Gerar slots de 30 em 30 minutos
            hora_atual = hora_inicio
            minuto_atual = minuto_inicio
            
            while hora_atual < hora_fim or (hora_atual == hora_fim and minuto_atual < minuto_fim):
                # Verificar se está no horário de almoço
                if tem_almoco:
                    if (hora_atual > almoco_inicio_hora or 
                        (hora_atual == almoco_inicio_hora and minuto_atual >= almoco_inicio_minuto)) and \
                       (hora_atual < almoco_fim_hora or 
                        (hora_atual == almoco_fim_hora and minuto_atual < almoco_fim_minuto)):
                        # Pular para depois do almoço
                        hora_atual = almoco_fim_hora
                        minuto_atual = almoco_fim_minuto
                        continue
                
                # Verificar se tem tempo suficiente para o serviço
                tempo_restante_minutos = (hora_fim - hora_atual) * 60 + (minuto_fim - minuto_atual)
                if tempo_restante_minutos >= service.duracao_minutos:
                    slots.append(f"{hora_atual:02d}:{minuto_atual:02d}")
                
                # Avançar 30 minutos
                minuto_atual += 30
                if minuto_atual >= 60:
                    hora_atual += 1
                    minuto_atual -= 60
            
            # Adicionar dia se tiver horários disponíveis
            if slots:
                # Nomes dos dias em português
                dias_semana = {
                    0: "Segunda-feira",
                    1: "Terça-feira", 
                    2: "Quarta-feira",
                    3: "Quinta-feira",
                    4: "Sexta-feira",
                    5: "Sábado",
                    6: "Domingo"
                }
                
                results.append({
                    "date": data.isoformat(),
                    "weekday": dias_semana[weekday],
                    "slots": slots
                })
        
        return JsonResponse({
            "results": results,
            "has_next": False,
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
