from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404, redirect, render
from .forms import AgendamentoForm
from .models import Agendamento
from .services import AvailabilityService, ConfirmacaoLinkService
from apps.core.mixins import AdminRequiredMixin, AdminOrClienteMixin, ClienteRequiredMixin
from apps.clientes.models import Cliente
from apps.profissionais.models import Profissional


class AgendamentoListView(AdminRequiredMixin, ListView):
    model = Agendamento
    template_name = "agendamentos/lista.html"
    context_object_name = "agendamentos"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'profissional', 'servico')

        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        cliente_filter = self.request.GET.get('cliente')
        if cliente_filter:
            queryset = queryset.filter(cliente_id=cliente_filter)

        profissional_filter = self.request.GET.get('profissional')
        if profissional_filter:
            queryset = queryset.filter(profissional_id=profissional_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Agendamento.Status.choices
        context['clientes'] = Cliente.objects.all().order_by('nome')
        context['profissionais'] = Profissional.objects.all().order_by('nome')
        context['filtro_status'] = self.request.GET.get('status', '')
        context['filtro_cliente'] = self.request.GET.get('cliente', '')
        context['filtro_profissional'] = self.request.GET.get('profissional', '')
        return context


class AgendamentoCreateView(AdminOrClienteMixin, CreateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = "agendamentos/form_clean.html"

    def get_success_url(self):
        if hasattr(self.request, 'cliente'):
            return reverse_lazy("meus_agendamentos")
        return reverse_lazy("agendamentos_lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request, 'cliente'):
            kwargs['user_cliente'] = self.request.cliente
        return kwargs

    def form_valid(self, form):
        if hasattr(self.request, 'cliente'):
            form.instance.cliente = self.request.cliente
            messages.success(self.request, "Agendamento solicitado com sucesso!")
        else:
            messages.success(self.request, "Agendamento criado com sucesso.")
        return super().form_valid(form)


class AgendamentoDeleteView(AdminOrClienteMixin, DeleteView):
    model = Agendamento
    template_name = "agendamentos/confirm_delete.html"

    def get_success_url(self):
        if hasattr(self.request, 'cliente'):
            return reverse_lazy("meus_agendamentos")
        return reverse_lazy("agendamentos_lista")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset
        if hasattr(self.request, 'cliente'):
            return queryset.filter(cliente=self.request.cliente)
        return queryset.none()

    def form_valid(self, form):
        if hasattr(self.request, 'cliente'):
            messages.success(self.request, "Agendamento cancelado com sucesso!")
        else:
            messages.success(self.request, "Agendamento removido com sucesso.")
        return super().form_valid(form)


class MeusAgendamentosView(ClienteRequiredMixin, ListView):
    model = Agendamento
    template_name = "agendamentos/meus_agendamentos.html"
    context_object_name = "agendamentos"

    def get_queryset(self):
        return Agendamento.objects.filter(
            cliente=self.request.cliente
        ).select_related('profissional', 'servico').order_by('data_hora_inicio')


class AgendamentoConcluirView(AdminRequiredMixin, View):
    """Transiciona AGENDADO/CONFIRMADO → CONCLUIDO. Exclusivo para admins."""

    def post(self, request, pk):
        agendamento = get_object_or_404(
            Agendamento,
            pk=pk,
            status__in=[Agendamento.Status.AGENDADO, Agendamento.Status.CONFIRMADO],
        )
        agendamento.status = Agendamento.Status.CONCLUIDO
        agendamento.save()
        messages.success(request, f'Agendamento #{pk} concluído com sucesso.')
        return redirect('agendamentos_lista')


class ResponderConfirmacaoView(View):
    """View pública (sem login). Exibe detalhes do agendamento e processa ação."""

    _TEMPLATE = "agendamentos/responder_confirmacao.html"

    def get(self, request, token):
        token_obj = ConfirmacaoLinkService.validar_token(token)
        if token_obj is None:
            return render(request, self._TEMPLATE, {"token_obj": None, "estado": "invalido"})

        agora = timezone.now()
        if token_obj.usado_em is not None:
            estado = "usado"
        elif token_obj.expires_at <= agora:
            estado = "expirado"
        else:
            estado = "valido"

        return render(request, self._TEMPLATE, {"token_obj": token_obj, "estado": estado})

    def post(self, request, token):
        token_obj = ConfirmacaoLinkService.validar_token(token)

        agora = timezone.now()
        if token_obj is None or token_obj.usado_em is not None or token_obj.expires_at <= agora:
            if token_obj is None:
                estado = "invalido"
            elif token_obj.usado_em:
                estado = "usado"
            else:
                estado = "expirado"
            return render(request, self._TEMPLATE, {"token_obj": token_obj, "estado": estado})

        acao = request.POST.get("acao")
        if acao not in ("CONFIRMADO", "CANCELADO"):
            return HttpResponseBadRequest("Ação inválida.")

        ConfirmacaoLinkService.processar(token_obj, acao)
        msg = "Agendamento confirmado com sucesso!" if acao == "CONFIRMADO" else "Agendamento cancelado com sucesso!"
        messages.success(request, msg)
        return redirect(reverse("responder_confirmacao", kwargs={"token": token}))


@require_POST
def confirmar_agendamento(request, pk):
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_cliente = request.user.is_authenticated and request.user.is_active and not request.user.is_staff

    if not is_admin and not is_cliente:
        messages.error(request, 'Você precisa estar autenticado.')
        return redirect('clientes_login')

    try:
        if is_admin:
            agendamento = Agendamento.objects.get(pk=pk)
            redirect_url = 'agendamentos_lista'
        else:
            agendamento = Agendamento.objects.get(pk=pk, cliente=request.user.perfil)
            redirect_url = 'meus_agendamentos'

        if agendamento.status != Agendamento.Status.AGENDADO:
            messages.error(request, 'Apenas agendamentos com status "Agendado" podem ser confirmados.')
        else:
            agendamento.status = Agendamento.Status.CONFIRMADO
            agendamento.save()
            messages.success(request, 'Agendamento confirmado com sucesso!')

    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        redirect_url = 'agendamentos_lista' if is_admin else 'meus_agendamentos'

    return redirect(redirect_url)


@require_POST
def cancelar_agendamento(request, pk):
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_cliente = request.user.is_authenticated and request.user.is_active and not request.user.is_staff

    if not is_admin and not is_cliente:
        messages.error(request, 'Você precisa estar autenticado.')
        return redirect('clientes_login')

    try:
        if is_admin:
            agendamento = Agendamento.objects.get(pk=pk)
            redirect_url = 'agendamentos_lista'
        else:
            agendamento = Agendamento.objects.get(pk=pk, cliente=request.user.perfil)
            redirect_url = 'meus_agendamentos'

        if agendamento.status not in [Agendamento.Status.AGENDADO, Agendamento.Status.CONFIRMADO]:
            messages.error(request, 'Apenas agendamentos Agendados ou Confirmados podem ser cancelados.')
        else:
            agendamento.status = Agendamento.Status.CANCELADO
            agendamento.save()
            messages.success(request, 'Agendamento cancelado com sucesso!')

    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        redirect_url = 'agendamentos_lista' if is_admin else 'meus_agendamentos'

    return redirect(redirect_url)


@require_GET
def simple_final_availability(request):
    try:
        professional_id = int(request.GET.get('professional_id', 1))
        service_id = int(request.GET.get('service_id', 1))

        from apps.profissionais.models import ProfessionalSchedule
        from apps.servicos.models import Servico
        from datetime import datetime, timedelta

        try:
            professional = Profissional.objects.get(id=professional_id, ativo=True)
            service = Servico.objects.get(id=service_id)
        except Exception:
            return JsonResponse({'error': 'Profissional ou serviço não encontrado', 'results': [], 'has_next': False, 'has_previous': False})

        schedules = ProfessionalSchedule.objects.filter(profissional=professional, is_day_off=False).order_by('weekday')
        if not schedules:
            return JsonResponse({'results': [], 'has_next': False, 'has_previous': False})

        schedules_por_weekday = {s.weekday: s for s in schedules}
        hoje = datetime.now().date()
        dias_semana = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
        results = []

        for weekday_banco, schedule in schedules_por_weekday.items():
            dias_para_frente = (weekday_banco - hoje.weekday() + 7) % 7
            data = hoje + timedelta(days=dias_para_frente)

            hora_atual, minuto_atual = schedule.start_time.hour, schedule.start_time.minute
            hora_fim, minuto_fim = schedule.end_time.hour, schedule.end_time.minute
            tem_almoco = schedule.lunch_start and schedule.lunch_end
            agora = datetime.now()
            limite_minimo = agora + timedelta(minutes=30)
            slots = []

            while hora_atual < hora_fim or (hora_atual == hora_fim and minuto_atual < minuto_fim):
                if tem_almoco and hora_atual == schedule.lunch_start.hour:
                    hora_atual, minuto_atual = schedule.lunch_end.hour, schedule.lunch_end.minute
                    continue
                tempo_restante = (hora_fim - hora_atual) * 60 + (minuto_fim - minuto_atual)
                if tempo_restante >= service.duracao_minutos:
                    dt_inicio = datetime(data.year, data.month, data.day, hora_atual, minuto_atual)
                    if dt_inicio >= limite_minimo:
                        existe = Agendamento.objects.filter(profissional=professional, data_hora_inicio=dt_inicio).exists()
                        if not existe:
                            slots.append(f"{hora_atual:02d}:{minuto_atual:02d}")
                minuto_atual += 30
                if minuto_atual >= 60:
                    hora_atual += 1
                    minuto_atual -= 60

            if slots:
                results.append({"date": data.isoformat(), "weekday": dias_semana[weekday_banco], "slots": slots})

        results.sort(key=lambda x: x["date"])
        return JsonResponse({"results": results, "has_next": False, "has_previous": False, "current_page": 1})

    except Exception as e:
        return JsonResponse({'error': str(e), 'results': [], 'has_next': False, 'has_previous': False}, status=500)


@require_GET
def availability_api_view(request):
    professional_id = request.GET.get('professional_id')
    service_id = request.GET.get('service_id')
    page = request.GET.get('page', 1)

    if not professional_id or not service_id:
        return JsonResponse({
            'error': 'professional_id and service_id are required',
            'results': [], 'has_next': False, 'has_previous': False,
        }, status=400)

    try:
        professional_id = int(professional_id)
        service_id = int(service_id)
        page = max(1, int(page))
    except ValueError:
        return JsonResponse({
            'error': 'Invalid parameter values',
            'results': [], 'has_next': False, 'has_previous': False,
        }, status=400)

    availability_data = AvailabilityService.get_available_slots(
        professional_id=professional_id,
        service_id=service_id,
        page=page,
    )
    return JsonResponse(availability_data)
