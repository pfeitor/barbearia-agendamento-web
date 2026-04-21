from django.urls import path
from .views import (
    AgendamentoCreateView, 
    AgendamentoDeleteView, 
    AgendamentoListView, 
    MeusAgendamentosView,
    availability_api_view,
    confirmar_agendamento,
    cancelar_agendamento
)
from .views_simple_final import simple_final_availability

urlpatterns = [
    # URLs administrativas
    path("", AgendamentoListView.as_view(), name="agendamentos_lista"),
    path("novo/", AgendamentoCreateView.as_view(), name="agendamentos_create"),
    path("<int:pk>/excluir/", AgendamentoDeleteView.as_view(), name="agendamentos_excluir"),
    
    # URLs do cliente
    path("meus-agendamentos/", MeusAgendamentosView.as_view(), name="meus_agendamentos"),
    path("<int:pk>/confirmar/", confirmar_agendamento, name="confirmar_agendamento"),
    path("<int:pk>/cancelar/", cancelar_agendamento, name="cancelar_agendamento"),
    
    # API endpoints
    path("availability/", availability_api_view, name="availability_api"),
    path("simple-final-availability/", simple_final_availability, name="simple_final_availability"),
]
