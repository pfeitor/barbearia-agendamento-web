from django.urls import path
from .views import ProfissionalCreateView, ProfissionalDeleteView, ProfissionalListView, ProfissionalUpdateView

urlpatterns = [
    path("", ProfissionalListView.as_view(), name="profissionais_lista"),
    path("novo/", ProfissionalCreateView.as_view(), name="profissionais_novo"),
    path("<int:pk>/editar/", ProfissionalUpdateView.as_view(), name="profissionais_editar"),
    path("<int:pk>/excluir/", ProfissionalDeleteView.as_view(), name="profissionais_excluir"),
]
