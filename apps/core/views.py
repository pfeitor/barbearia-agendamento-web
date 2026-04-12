from django.contrib.auth import login, logout
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from django.utils import timezone

from .mixins import ClienteRequiredMixin, AdminRequiredMixin
from .forms import ClienteLoginForm, AdminLoginForm
from .backends import TelefoneBackend, AdminEmailBackend
from apps.clientes.models import Cliente


class HomeView(TemplateView):
    """View principal - redireciona conforme autenticação."""
    template_name = "core/home.html"
    
    def dispatch(self, request, *args, **kwargs):
        # Cliente autenticado
        if 'cliente_id' in request.session:
            try:
                cliente = Cliente.objects.get(id=request.session['cliente_id'])
                request.cliente = cliente
                return render(request, "core/cliente_dashboard.html", {
                    'cliente': cliente,
                    'agendamentos': cliente.agendamentos.all().order_by('data_hora_inicio')
                })
            except Cliente.DoesNotExist:
                if 'cliente_id' in request.session:
                    del request.session['cliente_id']
        
        # Admin autenticado
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_dashboard')
        
        # Não autenticado - mostra login do cliente
        return redirect('login_cliente')


class ClienteLoginView(FormView):
    """Login de cliente por telefone."""
    template_name = "core/login_cliente.html"
    form_class = ClienteLoginForm
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        telefone = form.cleaned_data['telefone']
        
        try:
            cliente = Cliente.objects.get(telefone=telefone)
            # Cliente existe - faz login
            self.request.session['cliente_id'] = cliente.id
            messages.success(self.request, f"Bem-vindo(a), {cliente.nome}!")
            return super().form_valid(form)
        except Cliente.DoesNotExist:
            # Cliente não existe - redireciona para cadastro
            self.request.session['telefone_cadastro'] = telefone
            messages.info(self.request, f"Telefone {telefone} não encontrado. Cadastre-se abaixo.")
            return redirect('clientes_create')
    
    def form_invalid(self, form):
        messages.error(self.request, "Telefone inválido. Tente novamente.")
        return super().form_invalid(form)


class ClienteLogoutView(TemplateView):
    """Logout de cliente."""
    template_name = "core/login_cliente.html"
    
    def dispatch(self, request, *args, **kwargs):
        if 'cliente_id' in request.session:
            del request.session['cliente_id']
            messages.success(request, "Você saiu do sistema.")
        return redirect('login_cliente')


class AdminLoginView(FormView):
    """Login de administrador por email e senha."""
    template_name = "core/login_admin.html"
    form_class = AdminLoginForm
    success_url = reverse_lazy('admin_dashboard')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        backend = AdminEmailBackend()
        user = backend.authenticate(self.request, email=email, password=password)
        
        if user:
            login(self.request, user, backend='apps.core.backends.AdminEmailBackend')
            messages.success(self.request, f"Bem-vindo(a), {user.get_full_name() or user.username}!")
            return super().form_valid(form)
        else:
            form.add_error(None, "Email ou senha inválidos.")
            return self.form_invalid(form)


class AdminLogoutView(DjangoLogoutView):
    """Logout de administrador."""
    next_page = 'login_admin'
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Você saiu do painel administrativo.")
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Dashboard administrativo."""
    template_name = "core/admin_dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.clientes.models import Cliente
        from apps.agendamentos.models import Agendamento
        
        context.update({
            'total_clientes': Cliente.objects.count(),
            'total_agendamentos': Agendamento.objects.count(),
            'agendamentos_hoje': Agendamento.objects.filter(
                data_hora_inicio__date=timezone.now().date()
            ).count(),
            'agendamentos_recentes': Agendamento.objects.select_related(
                'cliente', 'profissional', 'servico'
            ).order_by('-created_at')[:10]
        })
        return context


def permission_denied(request, exception):
    """View customizada para erro 403."""
    from django.shortcuts import render
    return render(request, 'core/403.html', status=403)
