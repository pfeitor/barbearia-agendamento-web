from django.urls import path
from .views import lista_agendamentos

urlpatterns = [
    path("", lista_agendamentos, name="lista_agendamentos"),
]
