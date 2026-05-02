from django.urls import path

from .views import (
    AgendamentoConcluirView,
    AgendamentoCreateView,
    AgendamentoDeleteView,
    AgendamentoListView,
    MeusAgendamentosView,
    ResponderConfirmacaoView,
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

    # Confirmação por link (público, sem login)
    path("responder/<str:token>/", ResponderConfirmacaoView.as_view(), name="responder_confirmacao"),

    # API de disponibilidade
    path("availability/", availability_api_view, name="availability_api"),
    path("simple-final-availability/", simple_final_availability, name="simple_final_availability"),
]
