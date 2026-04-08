from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.core.urls")),
    path("clientes/", include("apps.clientes.urls")),
    path("profissionais/", include("apps.profissionais.urls")),
    path("servicos/", include("apps.servicos.urls")),
    path("agendamentos/", include("apps.agendamentos.urls")),
]
