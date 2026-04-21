"""Unit tests for AvailabilityService functionality."""

from datetime import datetime, timedelta, time, date
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache

from apps.agendamentos.services import AvailabilityService, TimeSlot
from apps.agendamentos.services_fixed import AvailabilityService as FixedAvailabilityService
from apps.profissionais.models import Profissional, ProfessionalSchedule
from apps.servicos.models import Servico
from apps.agendamentos.models import Agendamento


class TimeSlotTest(TestCase):
    """Test TimeSlot class functionality."""
    
    def test_duration_minutes(self):
        """Test duration calculation."""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 11, 30)
        slot = TimeSlot(start, end)
        self.assertEqual(slot.duration_minutes(), 90)
    
    def test_can_fit_service(self):
        """Test service duration fitting."""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 11, 0)
        slot = TimeSlot(start, end)
        
        self.assertTrue(slot.can_fit_service(60))
        self.assertTrue(slot.can_fit_service(30))
        self.assertFalse(slot.can_fit_service(90))
    
    def test_overlaps_with(self):
        """Test overlap detection."""
        slot1 = TimeSlot(
            datetime(2024, 1, 1, 10, 0),
            datetime(2024, 1, 1, 11, 0)
        )
        slot2 = TimeSlot(
            datetime(2024, 1, 1, 10, 30),
            datetime(2024, 1, 1, 11, 30)
        )
        slot3 = TimeSlot(
            datetime(2024, 1, 1, 11, 0),
            datetime(2024, 1, 1, 12, 0)
        )
        
        self.assertTrue(slot1.overlaps_with(slot2))
        self.assertFalse(slot1.overlaps_with(slot3))


class AvailabilityServiceTest(TestCase):
    """Test AvailabilityService functionality."""
    
    def setUp(self):
        """Set up test data."""
        cache.clear()
        
        # Create test professional
        self.professional = Profissional.objects.create(
            nome="Test Professional",
            ativo=True
        )
        
        # Create test service
        self.service = Servico.objects.create(
            nome="Haircut",
            duracao_minutos=30,
            preco=50.00
        )
        
        # Create schedule for Monday (weekday=0)
        self.schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=0,  # Monday
            start_time=time(9, 0),
            end_time=time(18, 0),
            lunch_start=time(12, 0),
            lunch_end=time(13, 0)
        )
    
    def test_merge_overlapping_intervals(self):
        """Test merging overlapping intervals."""
        intervals = [
            TimeSlot(datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 11, 0)),
            TimeSlot(datetime(2024, 1, 1, 10, 30), datetime(2024, 1, 1, 11, 30)),  # Overlaps
            TimeSlot(datetime(2024, 1, 1, 12, 0), datetime(2024, 1, 1, 13, 0)),  # Separate
            TimeSlot(datetime(2024, 1, 1, 12, 30), datetime(2024, 1, 1, 13, 30),)  # Overlaps with previous
        ]
        
        merged = FixedAvailabilityService._merge_overlapping_intervals(intervals)
        
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].start, datetime(2024, 1, 1, 10, 0))
        self.assertEqual(merged[0].end, datetime(2024, 1, 1, 11, 30))
        self.assertEqual(merged[1].start, datetime(2024, 1, 1, 12, 0))
        self.assertEqual(merged[1].end, datetime(2024, 1, 1, 13, 30))
    
    def test_subtract_intervals_fixed_no_overlap(self):
        """Test subtraction with non-overlapping intervals."""
        base = TimeSlot(datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 1, 18, 0))
        busy = [
            TimeSlot(datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 11, 0)),
            TimeSlot(datetime(2024, 1, 1, 14, 0), datetime(2024, 1, 1, 15, 0))
        ]
        
        free = FixedAvailabilityService._subtract_intervals_fixed(base, busy)
        
        self.assertEqual(len(free), 3)
        self.assertEqual(free[0].start, datetime(2024, 1, 1, 9, 0))
        self.assertEqual(free[0].end, datetime(2024, 1, 1, 10, 0))
        self.assertEqual(free[1].start, datetime(2024, 1, 1, 11, 0))
        self.assertEqual(free[1].end, datetime(2024, 1, 1, 14, 0))
        self.assertEqual(free[2].start, datetime(2024, 1, 1, 15, 0))
        self.assertEqual(free[2].end, datetime(2024, 1, 1, 18, 0))
    
    def test_subtract_intervals_fixed_with_overlap(self):
        """Test subtraction with overlapping intervals."""
        base = TimeSlot(datetime(2024, 1, 1, 9, 0), datetime(2024, 1, 1, 18, 0))
        busy = [
            TimeSlot(datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 11, 30)),
            TimeSlot(datetime(2024, 1, 1, 11, 0), datetime(2024, 1, 1, 12, 0)),  # Overlaps
        ]
        
        free = FixedAvailabilityService._subtract_intervals_fixed(base, busy)
        
        self.assertEqual(len(free), 2)
        self.assertEqual(free[0].start, datetime(2024, 1, 1, 9, 0))
        self.assertEqual(free[0].end, datetime(2024, 1, 1, 10, 0))
        self.assertEqual(free[1].start, datetime(2024, 1, 1, 12, 0))
        self.assertEqual(free[1].end, datetime(2024, 1, 1, 18, 0))
    
    def test_generate_slots_from_interval(self):
        """Test slot generation from free interval."""
        interval = TimeSlot(
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 11, 0)
        )
        
        slots = FixedAvailabilityService._generate_slots_from_interval(interval, 30)
        
        self.assertEqual(len(slots), 4)
        self.assertEqual(slots[0], datetime(2024, 1, 1, 9, 0))
        self.assertEqual(slots[1], datetime(2024, 1, 1, 9, 30))
        self.assertEqual(slots[2], datetime(2024, 1, 1, 10, 0))
        self.assertEqual(slots[3], datetime(2024, 1, 1, 10, 30))
    
    def test_generate_slots_insufficient_duration(self):
        """Test slot generation with insufficient duration."""
        interval = TimeSlot(
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 20)  # Only 20 minutes
        )
        
        slots = FixedAvailabilityService._generate_slots_from_interval(interval, 30)
        
        self.assertEqual(len(slots), 0)
    
    @patch('apps.agendamentos.services_fixed.timezone')
    def test_get_available_slots_for_day_with_appointments(self, mock_timezone):
        """Test slot calculation with existing appointments."""
        # Mock current date/time
        test_date = date(2024, 1, 1)  # Monday
        mock_timezone.now.return_value = datetime(2024, 1, 1, 8, 0)
        
        # Create appointment that blocks 10:00-10:30
        appointment = Mock()
        appointment.data_hora_inicio = datetime(2024, 1, 1, 10, 0)
        appointment.servico.duracao_minutos = 30
        
        with patch('apps.agendamentos.services_fixed.Agendamento.objects.filter') as mock_filter:
            mock_filter.return_value = [appointment]
            
            slots = FixedAvailabilityService._get_available_slots_for_day(
                self.professional, self.service, test_date
            )
            
            # Should not include 10:00 slot due to appointment
            slot_times = [slot.strftime("%H:%M") for slot in slots]
            self.assertNotIn("10:00", slot_times)
            self.assertIn("09:00", slot_times)
            self.assertIn("10:30", slot_times)
    
    def test_get_available_slots_day_off(self):
        """Test slot calculation for day off."""
        # Create day off schedule
        day_off_schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=1,  # Tuesday
            is_day_off=True
        )
        
        test_date = date(2024, 1, 2)  # Tuesday
        
        slots = FixedAvailabilityService._get_available_slots_for_day(
            self.professional, self.service, test_date
        )
        
        self.assertEqual(len(slots), 0)
    
    def test_get_available_slots_with_lunch_break(self):
        """Test slot calculation respecting lunch break."""
        test_date = date(2024, 1, 1)  # Monday
        
        with patch('apps.agendamentos.services_fixed.timezone') as mock_timezone:
            mock_timezone.now.return_value = datetime(2024, 1, 1, 8, 0)
            
            slots = FixedAvailabilityService._get_available_slots_for_day(
                self.professional, self.service, test_date
            )
            
            slot_times = [slot.strftime("%H:%M") for slot in slots]
            
            # Should not have slots during lunch (12:00-13:00)
            self.assertNotIn("12:00", slot_times)
            self.assertNotIn("12:30", slot_times)
            
            # Should have slots before and after lunch
            self.assertIn("11:30", slot_times)
            self.assertIn("13:00", slot_times)
    
    @patch('apps.agendamentos.services_fixed.timezone')
    def test_get_available_slots_today_adjustment(self, mock_timezone):
        """Test slot calculation for today with time adjustment."""
        test_date = date(2024, 1, 1)  # Monday
        mock_timezone.now.return_value = datetime(2024, 1, 1, 10, 15)
        
        slots = FixedAvailabilityService._get_available_slots_for_day(
            self.professional, self.service, test_date
        )
        
        slot_times = [slot.strftime("%H:%M") for slot in slots]
        
        # Should not have slots before current time
        self.assertNotIn("09:00", slot_times)
        self.assertNotIn("09:30", slot_times)
        self.assertNotIn("10:00", slot_times)
        
        # Should have slots after current time
        self.assertIn("10:30", slot_times)
    
    def test_get_available_slots_invalid_professional(self):
        """Test with invalid professional ID."""
        result = FixedAvailabilityService.get_available_slots(999, self.service.id)
        
        self.assertEqual(result["results"], [])
        self.assertFalse(result["has_next"])
        self.assertFalse(result["has_previous"])
    
    def test_get_available_slots_invalid_service(self):
        """Test with invalid service ID."""
        result = FixedAvailabilityService.get_available_slots(self.professional.id, 999)
        
        self.assertEqual(result["results"], [])
        self.assertFalse(result["has_next"])
        self.assertFalse(result["has_previous"])
    
    @patch('apps.agendamentos.services_fixed.timezone')
    def test_cache_functionality(self, mock_timezone):
        """Test caching behavior."""
        mock_timezone.now.return_value = datetime(2024, 1, 1, 8, 0)
        
        # First call should calculate
        result1 = FixedAvailabilityService.get_available_slots(
            self.professional.id, self.service.id
        )
        
        # Second call should use cache
        result2 = FixedAvailabilityService.get_available_slots(
            self.professional.id, self.service.id
        )
        
        self.assertEqual(result1, result2)


class EdgeCaseTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test data."""
        self.professional = Profissional.objects.create(
            nome="Test Professional",
            ativo=True
        )
        self.service = Servico.objects.create(
            nome="Haircut",
            duracao_minutos=60,
            preco=50.00
        )
    
    def test_exact_boundary_slots(self):
        """Test slots at exact boundaries."""
        # Schedule: 09:00-12:00, service: 60 minutes
        schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        test_date = date(2024, 1, 1)  # Monday
        
        with patch('apps.agendamentos.services_fixed.timezone') as mock_timezone:
            mock_timezone.now.return_value = datetime(2024, 1, 1, 8, 0)
            
            slots = FixedAvailabilityService._get_available_slots_for_day(
                self.professional, self.service, test_date
            )
            
            slot_times = [slot.strftime("%H:%M") for slot in slots]
            
            # Should include 09:00 and 10:00, but not 11:00 (would end at 12:00 exactly)
            self.assertIn("09:00", slot_times)
            self.assertIn("10:00", slot_times)
            self.assertNotIn("11:00", slot_times)
    
    def test_zero_duration_service(self):
        """Test with zero duration service (should be handled by model validation)."""
        # This would fail at model level due to MinValueValidator
        pass
    
    def test_service_longer_than_workday(self):
        """Test service longer than available workday."""
        # Create 8-hour service
        long_service = Servico.objects.create(
            nome="Long Treatment",
            duracao_minutos=480,  # 8 hours
            preco=200.00
        )
        
        # 4-hour workday
        schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(13, 0)
        )
        
        test_date = date(2024, 1, 1)  # Monday
        
        with patch('apps.agendamentos.services_fixed.timezone') as mock_timezone:
            mock_timezone.now.return_value = datetime(2024, 1, 1, 8, 0)
            
            slots = FixedAvailabilityService._get_available_slots_for_day(
                self.professional, long_service, test_date
            )
            
            self.assertEqual(len(slots), 0)
    
    def test_adjacent_appointments(self):
        """Test with appointments that are exactly adjacent."""
        # Create appointments: 09:00-10:00 and 10:00-11:00
        schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        test_date = date(2024, 1, 1)  # Monday
        
        # Mock two adjacent appointments
        appointment1 = Mock()
        appointment1.data_hora_inicio = datetime(2024, 1, 1, 9, 0)
        appointment1.servico.duracao_minutos = 60
        
        appointment2 = Mock()
        appointment2.data_hora_inicio = datetime(2024, 1, 1, 10, 0)
        appointment2.servico.duracao_minutos = 60
        
        with patch('apps.agendamentos.services_fixed.timezone') as mock_timezone:
            mock_timezone.now.return_value = datetime(2024, 1, 1, 8, 0)
            
            with patch('apps.agendamentos.services_fixed.Agendamento.objects.filter') as mock_filter:
                mock_filter.return_value = [appointment1, appointment2]
                
                slots = FixedAvailabilityService._get_available_slots_for_day(
                    self.professional, self.service, test_date
                )
                
                # Should only have slot at 11:00
                slot_times = [slot.strftime("%H:%M") for slot in slots]
                self.assertEqual(len(slot_times), 1)
                self.assertIn("11:00", slot_times)
