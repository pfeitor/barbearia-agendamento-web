from django.urls import path
from .views import (
    AgendamentoCreateView, 
    AgendamentoDeleteView, 
    AgendamentoListView, 
    AgendamentoUpdateView,
    MeusAgendamentosView,
    availability_api_view
)

urlpatterns = [
    # URLs administrativas
    path("", AgendamentoListView.as_view(), name="agendamentos_lista"),
    path("novo/", AgendamentoCreateView.as_view(), name="agendamentos_create"),
    path("<int:pk>/editar/", AgendamentoUpdateView.as_view(), name="agendamentos_editar"),
    path("<int:pk>/excluir/", AgendamentoDeleteView.as_view(), name="agendamentos_excluir"),
    
    # URLs do cliente
    path("meus-agendamentos/", MeusAgendamentosView.as_view(), name="meus_agendamentos"),
    
    # API endpoints
    path("availability/", availability_api_view, name="availability_api"),
]
