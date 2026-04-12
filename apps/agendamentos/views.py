from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.http import HttpResponseForbidden
from .forms import AgendamentoForm
from .models import Agendamento
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
    template_name = "agendamentos/form.html"
    
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
    template_name = "agendamentos/form.html"
    
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
