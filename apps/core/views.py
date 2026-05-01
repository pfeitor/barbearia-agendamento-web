from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect, render
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone

from .mixins import AdminRequiredMixin
from .forms import AdminLoginForm


class HomeView(TemplateView):
    """Redireciona conforme o tipo de autenticação."""
    template_name = "core/home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('admin_dashboard')

        if request.user.is_authenticated and request.user.is_active:
            try:
                cliente = request.user.perfil
                return render(request, "core/cliente_dashboard.html", {
                    'cliente': cliente,
                    'agendamentos': cliente.agendamentos.all().order_by('data_hora_inicio'),
                })
            except Exception:
                pass

        return redirect('clientes_login')


class AdminLoginView(FormView):
    template_name = "core/login_admin.html"
    form_class = AdminLoginForm
    success_url = reverse_lazy('admin_dashboard')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(self.request, email=email, password=password)

        if user and user.is_staff:
            login(self.request, user)
            messages.success(self.request, f"Bem-vindo(a)!")
            return super().form_valid(form)

        form.add_error(None, "E-mail ou senha inválidos.")
        return self.form_invalid(form)


class AdminLogoutView(DjangoLogoutView):
    next_page = 'login_admin'

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Você saiu do painel administrativo.")
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(AdminRequiredMixin, TemplateView):
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
            ).order_by('-created_at')[:10],
        })
        return context


def permission_denied(request, exception):
    return render(request, 'core/403.html', status=403)
