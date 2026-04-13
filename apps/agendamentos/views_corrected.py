"""Corrected availability - com conceito de weekdays corrigido"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

@require_GET
def corrected_availability(request):
    """Corrected availability - conceito de weekdays corrigido"""
    
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
        
        # Mapear schedules por weekday do banco
        schedules_por_weekday_banco = {}
        for schedule in schedules:
            schedules_por_weekday_banco[schedule.weekday] = schedule
        
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
        
        # Verificar quais weekdays têm schedules no banco
        weekdays_com_schedule = list(schedules_por_weekday_banco.keys())
        
        print(f"DEBUG: Weekdays com schedule no banco: {weekdays_com_schedule}")
        
        # Para cada weekday que tem schedule, encontrar a próxima data
        for weekday_banco in weekdays_com_schedule:
            # Encontrar a próxima data com este weekday (Python)
            dias_para_frente = (weekday_banco - hoje.weekday() + 7) % 7
            if dias_para_frente == 0:  # Se for hoje, verificar se ainda tem horário
                # Verificar se ainda tem horário disponível hoje
                agora_hora = datetime.now().hour
                schedule = schedules_por_weekday_banco[weekday_banco]
                if agora_hora >= schedule.end_time.hour:
                    dias_para_frente = 7  # Pular para próxima semana
                elif agora_hora >= schedule.end_time.hour - 1 and agora_hora < schedule.end_time.hour:
                    # Se estiver muito perto do fim, pular
                    dias_para_frente = 7
            
            data = hoje + timedelta(days=dias_para_frente)
            schedule = schedules_por_weekday_banco[weekday_banco]
            
            print(f"DEBUG: Weekday {weekday_banco} -> Data {data} ({dias_semana[weekday_banco]})")
            
            # Gerar horários
            slots = []
            hora_inicio = schedule.start_time.hour
            minuto_inicio = schedule.start_time.minute
            hora_fim = schedule.end_time.hour
            minuto_fim = schedule.end_time.minute
            
            # Se for hoje, pular horários já passados
            if dias_para_frente == 0:
                agora_hora = datetime.now().hour
                agora_minuto = datetime.now().minute
                if hora_inicio < agora_hora or (hora_inicio == agora_hora and minuto_inicio <= agora_minuto):
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
                    "weekday": dias_semana[weekday_banco],
                    "weekday_banco": weekday_banco,
                    "slots": slots
                })
        
        # Ordenar por data
        results.sort(key=lambda x: x["date"])
        
        print(f"DEBUG: Resultados finais: {[r['weekday'] for r in results]}")
        
        return JsonResponse({
            "results": results,
            "has_next": False,
            "has_previous": False,
            "current_page": 1
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"DEBUG: Erro: {e}")
        print(f"DEBUG: Traceback: {error_details}")
        
        return JsonResponse({
            'error': str(e),
            'details': error_details,
            'results': [],
            'has_next': False,
            'has_previous': False
        }, status=500)
