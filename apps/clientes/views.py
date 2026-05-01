from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.views.generic import DeleteView, FormView, ListView, TemplateView, UpdateView
from django.shortcuts import redirect

from .forms import (
    ClienteForm,
    ClienteLoginEmailForm,
    ClienteRegistroForm,
    EsqueciSenhaForm,
    NovaSenhaForm,
    VerificacaoEmailForm,
)
from .models import Cliente, ClienteUser
from .services import AuthService
from apps.core.mixins import AdminRequiredMixin, ClienteRequiredMixin


# ─── Admin CRUD ───────────────────────────────────────────────────────────────

class ClienteListView(AdminRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"


class ClienteCreateView(AdminRequiredMixin, FormView):
    """Criação de cliente via painel admin (sem vínculo a ClienteUser)."""
    template_name = "clientes/form.html"
    form_class = ClienteForm
    success_url = reverse_lazy('clientes_lista')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Cliente criado com sucesso.")
        return super().form_valid(form)


class ClienteUpdateView(AdminRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes_lista")

    def form_valid(self, form):
        messages.success(self.request, "Cliente atualizado com sucesso.")
        return super().form_valid(form)


class ClienteDeleteView(AdminRequiredMixin, DeleteView):
    model = Cliente
    template_name = "clientes/confirm_delete.html"
    success_url = reverse_lazy("clientes_lista")

    def form_valid(self, form):
        messages.success(self.request, "Cliente removido com sucesso.")
        return super().form_valid(form)


# ─── Perfil do cliente logado ─────────────────────────────────────────────────

class ClienteMeusDadosView(ClienteRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/meus_dados.html"
    success_url = reverse_lazy("meus_agendamentos")

    def get_object(self):
        return self.request.cliente

    def form_valid(self, form):
        messages.success(self.request, "Seus dados foram atualizados com sucesso.")
        return super().form_valid(form)


# ─── Registro ─────────────────────────────────────────────────────────────────

class ClienteRegisterView(FormView):
    template_name = "clientes/registrar.html"
    form_class = ClienteRegistroForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'perfil'):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cd = form.cleaned_data

        cliente_user = ClienteUser.objects.create_user(
            email=cd['email'],
            password=cd['senha'],
            is_active=False,
        )
        Cliente.objects.create(
            nome=cd['nome'],
            telefone=cd['telefone'],
            email=cd['email'],
            cliente_user=cliente_user,
        )

        try:
            AuthService.gerar_e_enviar_codigo(cliente_user)
        except ValueError as exc:
            messages.error(self.request, str(exc))
            cliente_user.delete()
            return self.form_invalid(form)

        self.request.session['verificacao_user_id'] = cliente_user.pk
        messages.info(self.request, f"Código enviado para {cd['email']}. Verifique sua caixa de entrada.")
        return redirect('verificar_email')


# ─── Verificação de e-mail ────────────────────────────────────────────────────

class VerificarEmailView(FormView):
    template_name = "clientes/verificar_email.html"
    form_class = VerificacaoEmailForm

    def dispatch(self, request, *args, **kwargs):
        if 'verificacao_user_id' not in request.session:
            return redirect('clientes_login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user_id = self.request.session.get('verificacao_user_id')
        codigo = form.cleaned_data['codigo']

        try:
            cliente_user = ClienteUser.objects.get(pk=user_id)
        except ClienteUser.DoesNotExist:
            messages.error(self.request, 'Sessão expirada. Registre-se novamente.')
            return redirect('clientes_registrar')

        if AuthService.verificar_codigo(cliente_user, codigo):
            del self.request.session['verificacao_user_id']
            login(self.request, cliente_user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(self.request, 'E-mail verificado! Bem-vindo(a)!')
            return redirect('home')

        messages.error(self.request, 'Código inválido ou expirado.')
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_id = self.request.session.get('verificacao_user_id')
        if user_id:
            try:
                ctx['email_destino'] = ClienteUser.objects.get(pk=user_id).email
            except ClienteUser.DoesNotExist:
                pass
        return ctx


class ReenviarCodigoView(TemplateView):
    """Recebe POST e reenvia o código de verificação."""

    def post(self, request, *args, **kwargs):
        user_id = request.session.get('verificacao_user_id')
        if not user_id:
            return redirect('clientes_login')

        try:
            cliente_user = ClienteUser.objects.get(pk=user_id)
            AuthService.gerar_e_enviar_codigo(cliente_user)
            messages.success(request, 'Novo código enviado para seu e-mail.')
        except ClienteUser.DoesNotExist:
            messages.error(request, 'Sessão expirada.')
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect('verificar_email')


# ─── Login / Logout ───────────────────────────────────────────────────────────

class ClienteLoginView(FormView):
    template_name = "clientes/login.html"
    form_class = ClienteLoginEmailForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff and request.user.is_active:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        senha = form.cleaned_data['senha']

        user = authenticate(self.request, email=email, password=senha)

        if user is None:
            form.add_error(None, 'E-mail ou senha inválidos.')
            return self.form_invalid(form)

        if not user.is_active:
            self.request.session['verificacao_user_id'] = user.pk
            messages.warning(self.request, 'Você ainda não verificou seu e-mail.')
            return redirect('verificar_email')

        if user.is_staff:
            form.add_error(None, 'Administradores devem usar o painel administrativo.')
            return self.form_invalid(form)

        login(self.request, user)
        messages.success(self.request, 'Bem-vindo(a)!')
        return redirect('home')


class ClienteLogoutView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'Você saiu do sistema.')
        return redirect('clientes_login')


# ─── Reset de senha ───────────────────────────────────────────────────────────

class EsqueciSenhaView(FormView):
    template_name = "clientes/esqueci_senha.html"
    form_class = EsqueciSenhaForm

    def form_valid(self, form):
        email = form.cleaned_data['email']

        try:
            cliente_user = ClienteUser.objects.get(email=email, is_staff=False)
            AuthService.enviar_link_reset(cliente_user, self.request)
        except ClienteUser.DoesNotExist:
            pass  # Não revela se o e-mail existe

        messages.success(
            self.request,
            'Se este e-mail estiver cadastrado, você receberá as instruções em breve.',
        )
        return redirect('clientes_login')


class ResetarSenhaView(FormView):
    template_name = "clientes/resetar_senha.html"
    form_class = NovaSenhaForm

    def dispatch(self, request, *args, **kwargs):
        self.cliente_user = AuthService.validar_token_reset(
            kwargs.get('uidb64'), kwargs.get('token')
        )
        if self.cliente_user is None:
            messages.error(request, 'Link inválido ou expirado.')
            return redirect('clientes_login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.cliente_user.set_password(form.cleaned_data['nova_senha'])
        self.cliente_user.is_active = True
        self.cliente_user.save(update_fields=['password', 'is_active'])
        messages.success(self.request, 'Senha redefinida com sucesso! Faça login.')
        return redirect('clientes_login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'uidb64': self.kwargs.get('uidb64'), 'token': self.kwargs.get('token')})
        return ctx
