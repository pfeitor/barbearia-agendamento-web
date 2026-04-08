from django.urls import path
from .views import AgendamentoCreateView, AgendamentoDeleteView, AgendamentoListView, AgendamentoUpdateView

urlpatterns = [
    path("", AgendamentoListView.as_view(), name="agendamentos_lista"),
    path("novo/", AgendamentoCreateView.as_view(), name="agendamentos_novo"),
    path("<int:pk>/editar/", AgendamentoUpdateView.as_view(), name="agendamentos_editar"),
    path("<int:pk>/excluir/", AgendamentoDeleteView.as_view(), name="agendamentos_excluir"),
]
