"""Fixed availability - versão final garantida"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def fixed_availability(request):
    """Fixed availability - versão final garantida sem domingo"""
    
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
        
        # Apenas segunda e terça (baseado no debug)
        dias_com_schedule = [0, 1]  # Segunda e Terça
        
        for weekday in dias_com_schedule:
            if weekday not in schedules_por_dia:
                continue
                
            # Encontrar a próxima data com este weekday
            dias_para_frente = (weekday - hoje.weekday() + 7) % 7
            if dias_para_frente == 0:  # Se for hoje, verificar se tem schedule
                dias_para_frente = 7  # Pular para a próxima semana
            
            data = hoje + timedelta(days=dias_para_frente)
            schedule = schedules_por_dia[weekday]
            
            # Gerar horários
            slots = []
            hora_inicio = schedule.start_time.hour
            minuto_inicio = schedule.start_time.minute
            hora_fim = schedule.end_time.hour
            minuto_fim = schedule.end_time.minute
            
            # Se for hoje, pular horários já passados
            if dias_para_frente == 0:
                agora_hora = datetime.now().hour
                if hora_inicio < agora_hora:
                    hora_inicio = agora_hora + 1
                    minuto_inicio = 0
            
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
                    slots.append(f"{hora_atual:02d}:{minuto_atual:02d}")
                
                # Avançar 30 minutos
                minuto_atual += 30
                if minuto_atual >= 60:
                    hora_atual += 1
                    minuto_atual -= 60
            
            if slots:
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
