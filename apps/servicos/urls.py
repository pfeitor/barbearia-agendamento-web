from django.urls import path
from .views import lista_servicos

urlpatterns = [
    path("", lista_servicos, name="lista_servicos"),
]
