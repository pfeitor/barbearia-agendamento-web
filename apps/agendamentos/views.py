from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from .forms import AgendamentoForm
from .models import Agendamento
from .services import AvailabilityService
from apps.core.mixins import AdminRequiredMixin, ClienteRequiredMixin, AdminOrClienteMixin


class AgendamentoListView(AdminRequiredMixin, ListView):
    """Listagem de agendamentos - apenas administradores."""
    model = Agendamento
    template_name = "agendamentos/lista.html"
    context_object_name = "agendamentos"


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


class AgendamentoUpdateView(AdminOrClienteMixin, UpdateView):
    """Atualização de agendamento - admin ou dono."""
    model = Agendamento
    form_class = AgendamentoForm
    template_name = "agendamentos/form_clean.html"
    
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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Se for cliente, filtra opções relevantes
        if hasattr(self.request, 'cliente'):
            kwargs['user_cliente'] = self.request.cliente
        return kwargs
    
    def form_valid(self, form):
        if hasattr(self.request, 'cliente'):
            messages.success(self.request, "Agendamento atualizado com sucesso!")
        else:
            messages.success(self.request, "Agendamento atualizado com sucesso.")
        
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
