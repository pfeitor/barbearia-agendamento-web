"""Signals for appointment management to clear availability cache."""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Agendamento
from .services import AvailabilityService


@receiver(post_save, sender=Agendamento)
def clear_availability_cache_on_save(sender, instance, created, **kwargs):
    """Clear availability cache when an appointment is created or updated."""
    # Clear cache for the professional and service involved
    AvailabilityService.clear_availability_cache(
        professional_id=instance.profissional.id,
        service_id=instance.servico.id
    )


@receiver(post_delete, sender=Agendamento)
def clear_availability_cache_on_delete(sender, instance, **kwargs):
    """Clear availability cache when an appointment is deleted."""
    # Clear cache for the professional and service involved
    AvailabilityService.clear_availability_cache(
        professional_id=instance.profissional.id,
        service_id=instance.servico.id
    )


@receiver(post_save, sender=Agendamento)
def notificar_novo_agendamento(sender, instance, created, **kwargs):
    """Envia e-mail de confirmação de recebimento quando um agendamento é criado."""
    if created:
        # Import lazy para evitar circular import entre apps
        from apps.notificacoes.services import NotificacaoService
        NotificacaoService.enviar_confirmacao_agendamento(instance)
