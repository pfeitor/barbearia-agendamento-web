from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


class ClienteRequiredMixin(AccessMixin):
    """Exige ClienteUser autenticado, ativo e com perfil (Cliente) vinculado."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_active:
            return self.handle_no_permission()

        if request.user.is_staff:
            return self.handle_no_permission()

        try:
            request.cliente = request.user.perfil
        except Exception:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def get_login_url(self):
        return '/clientes/login/'


class AdminRequiredMixin(AccessMixin):
    """Exige autenticação de administrador (is_staff=True)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_login_url(self):
        return '/login-admin/'


class ClienteQuerySetMixin:
    """Filtra queryset pelo cliente autenticado."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, 'cliente'):
            return queryset.filter(cliente=self.request.cliente)
        return queryset.none()


class AdminOrClienteMixin:
    """Permite acesso a admins ou ao cliente dono do recurso."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated or not request.user.is_active:
            return redirect('/clientes/login/')

        try:
            request.cliente = request.user.perfil
        except Exception:
            return redirect('/clientes/login/')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset

        if hasattr(self.request, 'cliente'):
            return queryset.filter(cliente=self.request.cliente)

        return queryset.none()
