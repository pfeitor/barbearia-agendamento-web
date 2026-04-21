from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from .forms import AgendamentoForm
from .models import Agendamento
from .services import AvailabilityService
from apps.core.mixins import AdminRequiredMixin, ClienteRequiredMixin, AdminOrClienteMixin
from apps.clientes.models import Cliente
from apps.profissionais.models import Profissional


class AgendamentoListView(AdminRequiredMixin, ListView):
    """Listagem de agendamentos - apenas administradores."""
    model = Agendamento
    template_name = "agendamentos/lista.html"
    context_object_name = "agendamentos"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'profissional', 'servico')
        
        # Filtro por status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtro por cliente
        cliente_filter = self.request.GET.get('cliente')
        if cliente_filter:
            queryset = queryset.filter(cliente_id=cliente_filter)
        
        # Filtro por profissional
        profissional_filter = self.request.GET.get('profissional')
        if profissional_filter:
            queryset = queryset.filter(profissional_id=profissional_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adicionar opções de filtros ao contexto
        context['status_choices'] = Agendamento.Status.choices
        context['clientes'] = Cliente.objects.all().order_by('nome')
        context['profissionais'] = Profissional.objects.all().order_by('nome')
        
        # Manter valores dos filtros selecionados
        context['filtro_status'] = self.request.GET.get('status', '')
        context['filtro_cliente'] = self.request.GET.get('cliente', '')
        context['filtro_profissional'] = self.request.GET.get('profissional', '')
        
        return context


class AgendamentoCreateView(AdminOrClienteMixin, CreateView):
    """Criação de agendamento - admin ou cliente."""
    model = Agendamento
    form_class = AgendamentoForm
    template_name = "agendamentos/form_clean.html"
    
    def get_success_url(self):
        # Cliente volta para seus agendamentos, admin para listagem
        if hasattr(self.request, 'cliente'):
            return reverse_lazy("meus_agendamentos")
        return reverse_lazy("agendamentos_lista")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Se for cliente, filtra opções relevantes
        if hasattr(self.request, 'cliente'):
            kwargs['user_cliente'] = self.request.cliente
        return kwargs
    
    def form_valid(self, form):
        # Se for cliente, define automaticamente o cliente do agendamento
        if hasattr(self.request, 'cliente'):
            form.instance.cliente = self.request.cliente
            messages.success(self.request, "Agendamento solicitado com sucesso!")
        else:
            messages.success(self.request, "Agendamento criado com sucesso.")
        
        return super().form_valid(form)




class AgendamentoDeleteView(AdminOrClienteMixin, DeleteView):
    """Exclusão de agendamento - admin ou dono."""
    model = Agendamento
    template_name = "agendamentos/confirm_delete.html"
    
    def get_success_url(self):
        if hasattr(self.request, 'cliente'):
            return reverse_lazy("meus_agendamentos")
        return reverse_lazy("agendamentos_lista")
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Admin vê tudo
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset
        
        # Cliente vê só os próprios
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
    """Meus agendamentos - apenas cliente logado."""
    model = Agendamento
    template_name = "agendamentos/meus_agendamentos.html"
    context_object_name = "agendamentos"
    
    def get_queryset(self):
        return Agendamento.objects.filter(
            cliente=self.request.cliente
        ).select_related('profissional', 'servico').order_by('data_hora_inicio')


@require_POST
def confirmar_agendamento(request, pk):
    """Confirmar um agendamento (mudar status de AGENDADO para CONFIRMADO)."""
    # Verificar se é admin ou cliente
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_cliente = 'cliente_id' in request.session
    
    if not is_admin and not is_cliente:
        messages.error(request, 'Você precisa estar logado como administrador ou cliente.')
        return redirect('/login-cliente/')
    
    try:
        if is_admin:
            # Admin pode confirmar qualquer agendamento
            agendamento = Agendamento.objects.get(pk=pk)
            redirect_url = 'agendamentos_lista'
        else:
            # Cliente só pode confirmar seus próprios agendamentos
            from apps.clientes.models import Cliente
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            agendamento = Agendamento.objects.get(pk=pk, cliente=cliente)
            redirect_url = 'meus_agendamentos'
        
        if agendamento.status != Agendamento.Status.AGENDADO:
            messages.error(request, 'Apenas agendamentos com status "Agendado" podem ser confirmados.')
        else:
            agendamento.status = Agendamento.Status.CONFIRMADO
            agendamento.save()
            messages.success(request, 'Agendamento confirmado com sucesso!')
            
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
    
    return redirect(redirect_url)


@require_POST
def cancelar_agendamento(request, pk):
    """Cancelar um agendamento (mudar status para CANCELADO)."""
    # Verificar se é admin ou cliente
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_cliente = 'cliente_id' in request.session
    
    if not is_admin and not is_cliente:
        messages.error(request, 'Você precisa estar logado como administrador ou cliente.')
        return redirect('/login-cliente/')
    
    try:
        if is_admin:
            # Admin pode cancelar qualquer agendamento
            agendamento = Agendamento.objects.get(pk=pk)
            redirect_url = 'agendamentos_lista'
        else:
            # Cliente só pode cancelar seus próprios agendamentos
            from apps.clientes.models import Cliente
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            agendamento = Agendamento.objects.get(pk=pk, cliente=cliente)
            redirect_url = 'meus_agendamentos'
        
        if agendamento.status not in [Agendamento.Status.AGENDADO, Agendamento.Status.CONFIRMADO]:
            messages.error(request, 'Apenas agendamentos com status "Agendado" ou "Confirmado" podem ser cancelados.')
        else:
            agendamento.status = Agendamento.Status.CANCELADO
            agendamento.save()
            messages.success(request, 'Agendamento cancelado com sucesso!')
            
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
    
    return redirect(redirect_url)


@require_GET
def availability_api_view(request):
    """
    API endpoint to get available time slots for a professional and service.
    
    Query Parameters:
    - professional_id: ID of the professional (required)
    - service_id: ID of the service (required)
    - page: Page number for pagination (default: 1)
    
    Returns:
    JSON response with available slots and pagination info
    """
    professional_id = request.GET.get('professional_id')
    service_id = request.GET.get('service_id')
    page = request.GET.get('page', 1)
    
    # Validate required parameters
    if not professional_id or not service_id:
        return JsonResponse({
            'error': 'professional_id and service_id are required',
            'results': [],
            'has_next': False,
            'has_previous': False
        }, status=400)
    
    try:
        professional_id = int(professional_id)
        service_id = int(service_id)
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        return JsonResponse({
            'error': 'Invalid parameter values',
            'results': [],
            'has_next': False,
            'has_previous': False
        }, status=400)
    
    # Get availability using the service
    availability_data = AvailabilityService.get_available_slots(
        professional_id=professional_id,
        service_id=service_id,
        page=page
    )
    
    return JsonResponse(availability_data)
