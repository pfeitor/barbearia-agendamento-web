from django.contrib import admin
from django.urls import include, path
from apps.core.urls import admin_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    # Remove login padrão do Django da navegação principal
    # path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.core.urls")),
    path("clientes/", include("apps.clientes.urls")),
    path("profissionais/", include("apps.profissionais.urls")),
    path("servicos/", include("apps.servicos.urls")),
    path("agendamentos/", include("apps.agendamentos.urls")),
    # URLs administrativas (acesso discreto)
] + admin_urls()
