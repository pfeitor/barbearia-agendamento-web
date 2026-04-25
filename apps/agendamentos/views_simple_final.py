"""API simples final - retorna dados com verificação de agendamentos existentes"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def simple_final_availability(request):
    """API simples final - retorna dados com verificação de agendamentos existentes"""
    
    try:
        professional_id = int(request.GET.get('professional_id', 1))
        service_id = int(request.GET.get('service_id', 1))
        
        # Importar modelos
        from apps.profissionais.models import Profissional, ProfessionalSchedule
        from apps.servicos.models import Servico
        from apps.agendamentos.models import Agendamento
        
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
        
        # Criar dicionário de schedules por weekday
        schedules_por_weekday = {}
        for schedule in schedules:
            schedules_por_weekday[schedule.weekday] = schedule
        
        hoje = datetime.now().date()
        results = []
        
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
        
        # Para cada weekday com schedule
        for weekday_banco in schedules_por_weekday.keys():
            # Encontrar a próxima data com este weekday (incluindo hoje)
            dias_para_frente = (weekday_banco - hoje.weekday() + 7) % 7
            
            data = hoje + timedelta(days=dias_para_frente)
            schedule = schedules_por_weekday[weekday_banco]
            
            # Gerar horários baseados no schedule
            slots = []
            hora_inicio = schedule.start_time.hour
            minuto_inicio = schedule.start_time.minute
            hora_fim = schedule.end_time.hour
            minuto_fim = schedule.end_time.minute
            
            # Verificar horário de almoço
            tem_almoco = schedule.lunch_start and schedule.lunch_end
            
            # Gerar slots de 30 em 30 minutos
            hora_atual = hora_inicio
            minuto_atual = minuto_inicio
            
            while hora_atual < hora_fim or (hora_atual == hora_fim and minuto_atual < minuto_fim):
                # Pular almoço
                if tem_almoco:
                    almoco_inicio_hora = schedule.lunch_start.hour
                    if hora_atual == almoco_inicio_hora:
                        hora_atual = schedule.lunch_end.hour
                        minuto_atual = schedule.lunch_end.minute
                        continue
                
                # Verificar se tem tempo suficiente
                tempo_restante = (hora_fim - hora_atual) * 60 + (minuto_fim - minuto_atual)
                if tempo_restante >= service.duracao_minutos:
                    slot_time = f"{hora_atual:02d}:{minuto_atual:02d}"
                    
                    # Verificar se este horário já está agendado
                    datetime_inicio = datetime.combine(data, datetime.min.time()).replace(
                        hour=hora_atual, minute=minuto_atual
                    )
                    
                    # Verificar se horário está no passado ou muito próximo (margem de 30 min)
                    agora = datetime.now()
                    limite_minimo = agora + timedelta(minutes=30)
                    
                    # Pular horários passados ou muito próximos
                    if datetime_inicio < limite_minimo:
                        # Avançar para próximo slot
                        minuto_atual += 30
                        if minuto_atual >= 60:
                            hora_atual += 1
                            minuto_atual -= 60
                        continue
                    
                    # Buscar agendamentos existentes para este profissional neste horário
                    agendamentos_existentes = Agendamento.objects.filter(
                        profissional=professional,
                        data_hora_inicio=datetime_inicio
                    ).exists()
                    
                    # Adicionar slot apenas se não estiver agendado
                    if not agendamentos_existentes:
                        slots.append(slot_time)
                
                # Avançar 30 minutos
                minuto_atual += 30
                if minuto_atual >= 60:
                    hora_atual += 1
                    minuto_atual -= 60
            
            if slots:
                results.append({
                    "date": data.isoformat(),
                    "weekday": dias_semana[weekday_banco],
                    "slots": slots
                })
        
        # Ordenar por data
        results.sort(key=lambda x: x["date"])
        
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
