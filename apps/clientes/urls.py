from django.urls import path
from .views import (
    ClienteCreateView, 
    ClienteDeleteView, 
    ClienteListView, 
    ClienteUpdateView,
    ClienteMeusDadosView
)

urlpatterns = [
    # URLs administrativas
    path("", ClienteListView.as_view(), name="clientes_lista"),
    path("novo/", ClienteCreateView.as_view(), name="clientes_create"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="clientes_editar"),
    path("<int:pk>/excluir/", ClienteDeleteView.as_view(), name="clientes_excluir"),
    
    # URLs do cliente
    path("meus-dados/", ClienteMeusDadosView.as_view(), name="meus_dados"),
]
