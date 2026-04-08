from django.urls import path
from .views import ServicoCreateView, ServicoDeleteView, ServicoListView, ServicoUpdateView

urlpatterns = [
    path("", ServicoListView.as_view(), name="servicos_lista"),
    path("novo/", ServicoCreateView.as_view(), name="servicos_novo"),
    path("<int:pk>/editar/", ServicoUpdateView.as_view(), name="servicos_editar"),
    path("<int:pk>/excluir/", ServicoDeleteView.as_view(), name="servicos_excluir"),
]
