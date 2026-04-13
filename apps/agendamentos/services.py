"""Availability calculation services for barber shop scheduling system."""

from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache

from apps.profissionais.models import Profissional, ProfessionalSchedule
from apps.servicos.models import Servico
from apps.agendamentos.models import Agendamento


class TimeSlot:
    """Represents a time slot with start and end times."""
    
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
    
    def duration_minutes(self) -> int:
        """Return duration in minutes."""
        return int((self.end - self.start).total_seconds() / 60)
    
    def can_fit_service(self, duration_minutes: int) -> bool:
        """Check if a service of given duration can fit in this slot."""
        return self.duration_minutes() >= duration_minutes
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this slot overlaps with another slot."""
        return self.start < other.end and other.start < self.end
    
    def __str__(self):
        return f"{self.start.strftime('%H:%M')} - {self.end.strftime('%H:%M')}"


class AvailabilityService:
    """Service for calculating professional availability."""
    
    SLOT_INTERVAL_MINUTES = 30  # Fixed interval for time slots
    
    @staticmethod
    def get_available_slots(
        professional_id: int, 
        service_id: int, 
        page: int = 1,
        days_per_page: int = 7
    ) -> Dict:
        """
        Get available time slots for a professional and service.
        
        Args:
            professional_id: ID of the professional
            service_id: ID of the service
            page: Page number for pagination
            days_per_page: Number of days to show per page
            
        Returns:
            Dict with results and pagination info
        """
        # Cache key for this request
        cache_key = f"availability_{professional_id}_{service_id}_{page}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            professional = Profissional.objects.get(id=professional_id, ativo=True)
            service = Servico.objects.get(id=service_id)
        except (Profissional.DoesNotExist, Servico.DoesNotExist):
            return {"results": [], "has_next": False, "has_previous": False}
        
        # Calculate date range for this page
        start_date = timezone.now().date() + timedelta(days=(page - 1) * days_per_page)
        end_date = start_date + timedelta(days=days_per_page - 1)
        
        available_days = []
        
        for current_date in AvailabilityService._date_range(start_date, end_date):
            # Skip past dates for today
            if current_date == timezone.now().date():
                current_time = timezone.now().time()
            else:
                current_time = time.min
            
            day_slots = AvailabilityService._get_available_slots_for_day(
                professional, service, current_date, current_time
            )
            
            if day_slots:  # Only include days with available slots
                available_days.append({
                    "date": current_date.isoformat(),
                    "weekday": current_date.strftime("%A"),
                    "slots": [slot.strftime("%H:%M") for slot in day_slots]
                })
        
        # Check if there are more days available
        has_next = AvailabilityService._has_availability_after(
            professional, service, end_date + timedelta(days=1)
        )
        has_previous = page > 1
        
        result = {
            "results": available_days,
            "has_next": has_next,
            "has_previous": has_previous,
            "current_page": page
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        return result
    
    @staticmethod
    def _get_available_slots_for_day(
        professional: Profissional, 
        service: Servico, 
        target_date: date,
        current_time: time = time.min
    ) -> List[datetime]:
        """Get available slots for a specific day."""
        weekday = target_date.weekday()
        
        try:
            schedule = ProfessionalSchedule.objects.get(
                profissional=professional,
                weekday=weekday
            )
        except ProfessionalSchedule.DoesNotExist:
            return []
        
        # Skip if it's a day off
        if schedule.is_day_off:
            return []
        
        # Get working hours for the day
        work_start = datetime.combine(target_date, schedule.start_time)
        work_end = datetime.combine(target_date, schedule.end_time)
        
        # Adjust for current time if it's today
        if target_date == timezone.now().date():
            now = timezone.now()
            if now > work_start:
                work_start = max(work_start, now)
        
        # Create busy intervals from existing appointments
        busy_intervals = AvailabilityService._get_busy_intervals(
            professional, target_date
        )
        
        # Create lunch break interval if exists
        lunch_intervals = []
        if schedule.lunch_start and schedule.lunch_end:
            lunch_start = datetime.combine(target_date, schedule.lunch_start)
            lunch_end = datetime.combine(target_date, schedule.lunch_end)
            lunch_intervals.append(TimeSlot(lunch_start, lunch_end))
        
        # Combine all busy intervals
        all_busy_intervals = busy_intervals + lunch_intervals
        
        # Generate free intervals by subtracting busy intervals from work hours
        free_intervals = AvailabilityService._subtract_intervals(
            TimeSlot(work_start, work_end),
            all_busy_intervals
        )
        
        # Generate valid slots from free intervals
        available_slots = []
        for interval in free_intervals:
            slots = AvailabilityService._generate_slots_from_interval(
                interval, service.duracao_minutos
            )
            available_slots.extend(slots)
        
        return available_slots
    
    @staticmethod
    def _get_busy_intervals(professional: Profissional, target_date: date) -> List[TimeSlot]:
        """Get busy intervals from existing appointments."""
        appointments = Agendamento.objects.filter(
            profissional=professional,
            data_hora_inicio__date=target_date,
            status__in=[Agendamento.Status.AGENDADO, Agendamento.Status.CONFIRMADO]
        ).select_related('servico')
        
        busy_intervals = []
        for appointment in appointments:
            start_time = appointment.data_hora_inicio
            end_time = start_time + timedelta(minutes=appointment.servico.duracao_minutos)
            busy_intervals.append(TimeSlot(start_time, end_time))
        
        return busy_intervals
    
    @staticmethod
    def _subtract_intervals(
        base_interval: TimeSlot, 
        intervals_to_subtract: List[TimeSlot]
    ) -> List[TimeSlot]:
        """Subtract multiple intervals from a base interval."""
        if not intervals_to_subtract:
            return [base_interval]
        
        # Sort intervals by start time
        intervals_to_subtract.sort(key=lambda x: x.start)
        
        result = []
        current_start = base_interval.start
        
        for interval in intervals_to_subtract:
            # If interval doesn't overlap, continue
            if interval.end <= current_start or interval.start >= base_interval.end:
                continue
            
            # Add free time before this busy interval
            if interval.start > current_start:
                result.append(TimeSlot(current_start, interval.start))
            
            # Update current start to after this busy interval
            current_start = max(current_start, interval.end)
        
        # Add remaining time after last busy interval
        if current_start < base_interval.end:
            result.append(TimeSlot(current_start, base_interval.end))
        
        return result
    
    @staticmethod
    def _generate_slots_from_interval(
        interval: TimeSlot, 
        service_duration: int
    ) -> List[datetime]:
        """Generate valid time slots from a free interval."""
        slots = []
        current_time = interval.start
        
        while current_time + timedelta(minutes=service_duration) <= interval.end:
            # Check if this slot fits exactly on the interval grid
            minutes_past_hour = current_time.minute
            if minutes_past_hour % AvailabilityService.SLOT_INTERVAL_MINUTES == 0:
                slots.append(current_time)
            
            current_time += timedelta(minutes=AvailabilityService.SLOT_INTERVAL_MINUTES)
        
        return slots
    
    @staticmethod
    def _date_range(start_date: date, end_date: date) -> List[date]:
        """Generate a list of dates from start to end (inclusive)."""
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates
    
    @staticmethod
    def _has_availability_after(
        professional: Profissional, 
        service: Servico, 
        check_date: date
    ) -> bool:
        """Check if there's any availability after a given date."""
        # Check next 14 days for availability
        for future_date in AvailabilityService._date_range(
            check_date, 
            check_date + timedelta(days=14)
        ):
            slots = AvailabilityService._get_available_slots_for_day(
                professional, service, future_date
            )
            if slots:
                return True
        return False
    
    @staticmethod
    def clear_availability_cache(professional_id: int, service_id: int = None):
        """Clear availability cache for a professional (and optionally service)."""
        if service_id:
            # Clear specific cache
            cache.delete(f"availability_{professional_id}_{service_id}_1")
        else:
            # Clear all caches for this professional
            keys = cache.keys(f"availability_{professional_id}_*")
            cache.delete_many(keys)
