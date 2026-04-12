from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from apps.clientes.models import Cliente


class ClienteRequiredMixin(AccessMixin):
    """Mixin que exige autenticação de cliente via telefone."""
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se há cliente na sessão
        if 'cliente_id' not in request.session:
            return self.handle_no_permission()
        
        try:
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            request.cliente = cliente
        except Cliente.DoesNotExist:
            # Limpa sessão inválida
            if 'cliente_id' in request.session:
                del request.session['cliente_id']
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_login_url(self):
        return '/login-cliente/'


class AdminRequiredMixin(AccessMixin):
    """Mixin que exige autenticação de administrador (staff/superuser)."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_login_url(self):
        return '/login-admin/'


class ClienteQuerySetMixin:
    """Mixin para filtrar queryset por cliente logado."""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, 'cliente'):
            return queryset.filter(cliente=self.request.cliente)
        return queryset.none()  # Segurança: não retorna nada se não houver cliente


class AdminOrClienteMixin:
    """Mixin que permite acesso admin ou cliente próprio."""
    
    def dispatch(self, request, *args, **kwargs):
        # Admin tem acesso total
        if request.user.is_authenticated and request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        
        # Cliente precisa estar autenticado
        if 'cliente_id' not in request.session:
            return redirect('/login-cliente/')
        
        try:
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            request.cliente = cliente
        except Cliente.DoesNotExist:
            if 'cliente_id' in request.session:
                del request.session['cliente_id']
            return redirect('/login-cliente/')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Admin vê tudo
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset
        
        # Cliente vê só os próprios
        if hasattr(self.request, 'cliente'):
            return queryset.filter(cliente=self.request.cliente)
        
        return queryset.none()
