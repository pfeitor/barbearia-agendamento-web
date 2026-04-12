from django.urls import path
from .views import (
    HomeView, 
    ClienteLoginView, 
    ClienteLogoutView, 
    AdminLoginView,
    AdminLogoutView,
    AdminDashboardView
)

urlpatterns = [
    # Fluxo principal do cliente
    path("", HomeView.as_view(), name="home"),
    path("login-cliente/", ClienteLoginView.as_view(), name="login_cliente"),
    path("logout-cliente/", ClienteLogoutView.as_view(), name="logout_cliente"),
    path("meus-agendamentos/", HomeView.as_view(), name="meus_agendamentos"),
    
    # Login administrativo (discreto)
    path("login-admin/", AdminLoginView.as_view(), name="login_admin"),
    path("logout-admin/", AdminLogoutView.as_view(), name="logout_admin"),
]

# URLs administrativas separadas (mantido para compatibilidade)
urlpatterns_admin = [
    path("", AdminDashboardView.as_view(), name="admin_dashboard"),
]

# Exportar para poder ser importado
__all__ = ['urlpatterns', 'urlpatterns_admin']

# Para incluir URLs admin no mesmo módulo, vamos criar uma função que retorna as URLs
def admin_urls():
    """Retorna URLs administrativas para inclusão."""
    return [
        path("painel/", AdminDashboardView.as_view(), name="admin_dashboard"),
    ]
