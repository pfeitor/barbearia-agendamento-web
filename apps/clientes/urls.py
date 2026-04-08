from django.urls import path
from .views import ClienteCreateView, ClienteDeleteView, ClienteListView, ClienteUpdateView

urlpatterns = [
    path("", ClienteListView.as_view(), name="clientes_lista"),
    path("novo/", ClienteCreateView.as_view(), name="clientes_novo"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="clientes_editar"),
    path("<int:pk>/excluir/", ClienteDeleteView.as_view(), name="clientes_excluir"),
]
