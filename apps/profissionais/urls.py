from django.urls import path
from .views import lista_profissionais

urlpatterns = [
    path("", lista_profissionais, name="lista_profissionais"),
]
