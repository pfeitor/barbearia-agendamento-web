from django.urls import path
from django.views.generic import RedirectView

from .views import AdminDashboardView, AdminLoginView, AdminLogoutView, HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    # Backward-compat: redireciona antigas URLs de login por telefone (301)
    path("login-cliente/", RedirectView.as_view(url='/clientes/login/', permanent=True), name="login_cliente"),
    path("logout-cliente/", RedirectView.as_view(url='/clientes/logout/', permanent=True), name="logout_cliente"),

    # Painel admin
    path("login-admin/", AdminLoginView.as_view(), name="login_admin"),
    path("logout-admin/", AdminLogoutView.as_view(), name="logout_admin"),
]


def admin_urls():
    return [
        path("painel/", AdminDashboardView.as_view(), name="admin_dashboard"),
    ]
