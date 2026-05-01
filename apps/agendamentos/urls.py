from django.urls import path

from .views import (
    AgendamentoConcluirView,
    AgendamentoCreateView,
    AgendamentoDeleteView,
    AgendamentoListView,
    MeusAgendamentosView,
    availability_api_view,
    cancelar_agendamento,
    confirmar_agendamento,
    simple_final_availability,
)

urlpatterns = [
    # Admin
    path("", AgendamentoListView.as_view(), name="agendamentos_lista"),
    path("novo/", AgendamentoCreateView.as_view(), name="agendamentos_create"),
    path("<int:pk>/excluir/", AgendamentoDeleteView.as_view(), name="agendamentos_excluir"),
    path("<int:pk>/concluir/", AgendamentoConcluirView.as_view(), name="concluir_agendamento"),

    # Cliente
    path("meus-agendamentos/", MeusAgendamentosView.as_view(), name="meus_agendamentos"),
    path("<int:pk>/confirmar/", confirmar_agendamento, name="confirmar_agendamento"),
    path("<int:pk>/cancelar/", cancelar_agendamento, name="cancelar_agendamento"),

    # API de disponibilidade
    path("availability/", availability_api_view, name="availability_api"),
    path("simple-final-availability/", simple_final_availability, name="simple_final_availability"),
]
