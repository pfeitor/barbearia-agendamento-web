from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.shortcuts import redirect
from .forms import ClienteForm
from .models import Cliente
from apps.core.mixins import AdminRequiredMixin, ClienteRequiredMixin


class ClienteListView(AdminRequiredMixin, ListView):
    """Listagem de clientes - apenas administradores."""
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"


class ClienteCreateView(CreateView):
    """Cadastro de cliente - público (fluxo de login)."""
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    
    def get_success_url(self):
        # Se veio do login, vai para home do cliente
        if 'telefone_cadastro' in self.request.session:
            return reverse_lazy('home')
        # Se for admin, vai para listagem
        return reverse_lazy('clientes_lista')
    
    def get_initial(self):
        initial = super().get_initial()
        # Preenche telefone se veio do fluxo de login
        if 'telefone_cadastro' in self.request.session:
            initial['telefone'] = self.request.session['telefone_cadastro']
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Se veio do login, autentica automaticamente
        if 'telefone_cadastro' in self.request.session:
            self.request.session['cliente_id'] = self.object.id
            messages.success(self.request, f"Bem-vindo(a), {self.object.nome}! Cadastro realizado com sucesso.")
            del self.request.session['telefone_cadastro']
        else:
            messages.success(self.request, "Cliente criado com sucesso.")
        
        return response


class ClienteUpdateView(AdminRequiredMixin, UpdateView):
    """Atualização de cliente - apenas administradores."""
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes_lista")

    def form_valid(self, form):
        messages.success(self.request, "Cliente atualizado com sucesso.")
        return super().form_valid(form)


class ClienteDeleteView(AdminRequiredMixin, DeleteView):
    """Exclusão de cliente - apenas administradores."""
    model = Cliente
    template_name = "clientes/confirm_delete.html"
    success_url = reverse_lazy("clientes_lista")

    def form_valid(self, form):
        messages.success(self.request, "Cliente removido com sucesso.")
        return super().form_valid(form)


class ClienteMeusDadosView(ClienteRequiredMixin, UpdateView):
    """Meus dados - apenas cliente logado pode editar seus próprios dados."""
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/meus_dados.html"
    success_url = reverse_lazy("meus_agendamentos")
    
    def get_object(self):
        # Sempre retorna o cliente logado
        return self.request.cliente
    
    def form_valid(self, form):
        messages.success(self.request, "Seus dados foram atualizados com sucesso.")
        return super().form_valid(form)
