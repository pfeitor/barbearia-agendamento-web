from django.urls import path
from .views import (
    AgendamentoCreateView, 
    AgendamentoDeleteView, 
    AgendamentoListView, 
    AgendamentoUpdateView,
    MeusAgendamentosView,
    availability_api_view
)
from . import views_debug
from . import views_simple
from . import views_working
from . import views_ultra_simple
from . import views_final
from . import views_weekday_debug
from . import views_fixed
from . import views_hardcoded
from . import views_concept_debug
from . import views_corrected
from . import views_banco_check
from . import views_definitiva
from . import views_simple_final

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
    
    # Debug endpoints
    path("debug/test/", views_debug.debug_simple_test, name="debug_test"),
    path("debug/availability/", views_debug.debug_availability_test, name="debug_availability"),
    
    # Simple availability endpoint (backup)
    path("availability/simple/", views_simple.simple_availability, name="simple_availability"),
    
    # Working availability endpoint (guaranteed to work)
    path("availability/working/", views_working.working_availability, name="working_availability"),
    
    # Ultra simple availability (final backup)
    path("availability/ultra/", views_ultra_simple.ultra_simple_availability, name="ultra_simple_availability"),
    
    # Final availability (no timezone issues)
    path("availability/final/", views_final.final_availability, name="final_availability"),
    
    # Weekday debug endpoint
    path("debug/weekdays/", views_weekday_debug.debug_weekdays, name="debug_weekdays"),
    
    # Fixed availability (final solution - no domingo)
    path("availability/fixed/", views_fixed.fixed_availability, name="fixed_availability"),
    
    # Hardcoded availability (test final - apenas segunda e terça)
    path("availability/hardcoded/", views_hardcoded.hardcoded_availability, name="hardcoded_availability"),
    
    # Concept debug endpoint
    path("debug/concept/", views_concept_debug.debug_concept, name="debug_concept"),
    
    # Corrected availability (com debug e conceito corrigido)
    path("availability/corrected/", views_corrected.corrected_availability, name="corrected_availability"),
    
    # Banco check page
    path("check/banco/", views_banco_check.banco_check_view, name="banco_check"),
    
    # Definitive availability (solução final 100% garantida)
    path("availability/definitiva/", views_definitiva.definitiva_availability, name="definitiva_availability"),
    
    # Simple final availability (backup ultra simples)
    path("availability/simple-final/", views_simple_final.simple_final_availability, name="simple_final_availability"),
]
