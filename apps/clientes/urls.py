from django.urls import path

from .views import (
    ClienteCreateView,
    ClienteDeleteView,
    ClienteListView,
    ClienteLoginView,
    ClienteLogoutView,
    ClienteMeusDadosView,
    ClienteRegisterView,
    ClienteUpdateView,
    EsqueciSenhaView,
    ReenviarCodigoView,
    ResetarSenhaView,
    VerificarEmailView,
)

urlpatterns = [
    # Admin CRUD
    path("", ClienteListView.as_view(), name="clientes_lista"),
    path("novo/", ClienteCreateView.as_view(), name="clientes_create"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="clientes_editar"),
    path("<int:pk>/excluir/", ClienteDeleteView.as_view(), name="clientes_excluir"),

    # Perfil do cliente logado
    path("meus-dados/", ClienteMeusDadosView.as_view(), name="meus_dados"),

    # Auth: registro e verificação de e-mail
    path("registrar/", ClienteRegisterView.as_view(), name="clientes_registrar"),
    path("verificar/", VerificarEmailView.as_view(), name="verificar_email"),
    path("reenviar-codigo/", ReenviarCodigoView.as_view(), name="reenviar_codigo"),

    # Auth: login / logout
    path("login/", ClienteLoginView.as_view(), name="clientes_login"),
    path("logout/", ClienteLogoutView.as_view(), name="clientes_logout"),

    # Auth: reset de senha
    path("esqueci-senha/", EsqueciSenhaView.as_view(), name="esqueci_senha"),
    path("resetar-senha/<uidb64>/<token>/", ResetarSenhaView.as_view(), name="resetar_senha"),
]
