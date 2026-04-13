"""Tests for the availability calculation system."""

from datetime import datetime, timedelta, time, date
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache

from apps.profissionais.models import Profissional, ProfessionalSchedule
from apps.clientes.models import Cliente
from apps.servicos.models import Servico
from apps.agendamentos.models import Agendamento
from apps.agendamentos.services import AvailabilityService, TimeSlot


class TimeSlotTests(TestCase):
    """Test the TimeSlot utility class."""
    
    def test_time_slot_creation(self):
        """Test creating a time slot."""
        start = datetime(2026, 4, 13, 9, 0)
        end = datetime(2026, 4, 13, 10, 0)
        slot = TimeSlot(start, end)
        
        self.assertEqual(slot.start, start)
        self.assertEqual(slot.end, end)
        self.assertEqual(slot.duration_minutes(), 60)
    
    def test_time_slot_duration(self):
        """Test duration calculation."""
        slot1 = TimeSlot(
            datetime(2026, 4, 13, 9, 0), 
            datetime(2026, 4, 13, 10, 0)
        )
        self.assertEqual(slot1.duration_minutes(), 60)
        
        slot2 = TimeSlot(
            datetime(2026, 4, 13, 9, 30), 
            datetime(2026, 4, 13, 10, 15)
        )
        self.assertEqual(slot2.duration_minutes(), 45)
    
    def test_can_fit_service(self):
        """Test if service can fit in slot."""
        slot = TimeSlot(
            datetime(2026, 4, 13, 9, 0), 
            datetime(2026, 4, 13, 10, 0)
        )
        
        self.assertTrue(slot.can_fit_service(30))
        self.assertTrue(slot.can_fit_service(60))
        self.assertFalse(slot.can_fit_service(61))
    
    def test_overlaps_with(self):
        """Test overlap detection."""
        slot1 = TimeSlot(
            datetime(2026, 4, 13, 9, 0), 
            datetime(2026, 4, 13, 10, 0)
        )
        
        # Overlapping slots
        overlapping1 = TimeSlot(
            datetime(2026, 4, 13, 9, 30), 
            datetime(2026, 4, 13, 10, 30)
        )
        overlapping2 = TimeSlot(
            datetime(2026, 4, 13, 8, 30), 
            datetime(2026, 4, 13, 9, 30)
        )
        
        # Non-overlapping slots
        non_overlapping1 = TimeSlot(
            datetime(2026, 4, 13, 8, 0), 
            datetime(2026, 4, 13, 9, 0)
        )
        non_overlapping2 = TimeSlot(
            datetime(2026, 4, 13, 10, 0), 
            datetime(2026, 4, 13, 11, 0)
        )
        
        self.assertTrue(slot1.overlaps_with(overlapping1))
        self.assertTrue(slot1.overlaps_with(overlapping2))
        self.assertFalse(slot1.overlaps_with(non_overlapping1))
        self.assertFalse(slot1.overlaps_with(non_overlapping2))


class AvailabilityServiceTests(TestCase):
    """Test the AvailabilityService class."""
    
    def setUp(self):
        """Set up test data."""
        cache.clear()
        
        # Create test professional
        self.professional = Profissional.objects.create(
            nome="João Barbeiro",
            ativo=True
        )
        
        # Create test service
        self.service = Servico.objects.create(
            nome="Corte de Cabelo",
            duracao_minutos=30,
            preco=50.00
        )
        
        # Create test client
        self.client = Cliente.objects.create(
            nome="Maria Cliente",
            email="maria@teste.com",
            telefone="11999999999"
        )
        
        # Create schedule for Monday (weekday 0)
        self.schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            lunch_start=time(12, 0),
            lunch_end=time(13, 0),
            is_day_off=False
        )
    
    def test_get_available_slots_no_schedule(self):
        """Test availability when no schedule exists."""
        # Test Tuesday (no schedule created)
        tuesday_date = date(2026, 4, 14)  # Tuesday
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, tuesday_date
        )
        
        self.assertEqual(len(slots), 0)
    
    def test_get_available_slots_day_off(self):
        """Test availability when it's a day off."""
        # Create day off schedule for Wednesday
        day_off_schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.WEDNESDAY,
            is_day_off=True
        )
        
        wednesday_date = date(2026, 4, 15)  # Wednesday
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, wednesday_date
        )
        
        self.assertEqual(len(slots), 0)
    
    def test_get_available_slots_basic(self):
        """Test basic availability calculation."""
        monday_date = date(2026, 4, 13)  # Monday
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, monday_date
        )
        
        # Should have slots from 9:00 to 12:00 and 13:00 to 17:30
        # 30-minute intervals, excluding lunch 12:00-13:00
        expected_morning_slots = [
            datetime(2026, 4, 13, 9, 0),
            datetime(2026, 4, 13, 9, 30),
            datetime(2026, 4, 13, 10, 0),
            datetime(2026, 4, 13, 10, 30),
            datetime(2026, 4, 13, 11, 0),
            datetime(2026, 4, 13, 11, 30),
        ]
        
        expected_afternoon_slots = [
            datetime(2026, 4, 13, 13, 0),
            datetime(2026, 4, 13, 13, 30),
            datetime(2026, 4, 13, 14, 0),
            datetime(2026, 4, 13, 14, 30),
            datetime(2026, 4, 13, 15, 0),
            datetime(2026, 4, 13, 15, 30),
            datetime(2026, 4, 13, 16, 0),
            datetime(2026, 4, 13, 16, 30),
            datetime(2026, 4, 13, 17, 0),
            datetime(2026, 4, 13, 17, 30),
        ]
        
        all_expected = expected_morning_slots + expected_afternoon_slots
        self.assertEqual(len(slots), len(all_expected))
        
        for expected_slot in all_expected:
            self.assertIn(expected_slot, slots)
    
    def test_get_available_slots_with_appointments(self):
        """Test availability with existing appointments."""
        monday_date = date(2026, 4, 13)  # Monday
        
        # Create an appointment at 9:00
        appointment = Agendamento.objects.create(
            data_hora_inicio=datetime(2026, 4, 13, 9, 0),
            cliente=self.client,
            profissional=self.professional,
            servico=self.service,
            status=Agendamento.Status.AGENDADO
        )
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, monday_date
        )
        
        # 9:00 slot should be blocked, but 9:30 should be available
        blocked_time = datetime(2026, 4, 13, 9, 0)
        next_available = datetime(2026, 4, 13, 9, 30)
        
        self.assertNotIn(blocked_time, slots)
        self.assertIn(next_available, slots)
    
    def test_get_available_slots_overlapping_appointments(self):
        """Test availability with overlapping appointments."""
        monday_date = date(2026, 4, 13)  # Monday
        
        # Create a 60-minute appointment at 10:00
        long_service = Servico.objects.create(
            nome="Corte e Barba",
            duracao_minutos=60,
            preco=80.00
        )
        
        appointment = Agendamento.objects.create(
            data_hora_inicio=datetime(2026, 4, 13, 10, 0),
            cliente=self.client,
            profissional=self.professional,
            servico=long_service,
            status=Agendamento.Status.AGENDADO
        )
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, monday_date
        )
        
        # 10:00 and 10:30 should be blocked
        self.assertNotIn(datetime(2026, 4, 13, 10, 0), slots)
        self.assertNotIn(datetime(2026, 4, 13, 10, 30), slots)
        # 11:00 should be available
        self.assertIn(datetime(2026, 4, 13, 11, 0), slots)
    
    def test_get_available_slots_lunch_break(self):
        """Test that lunch break blocks slots correctly."""
        monday_date = date(2026, 4, 13)  # Monday
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, monday_date
        )
        
        # Slots during lunch (12:00-13:00) should be blocked
        self.assertNotIn(datetime(2026, 4, 13, 12, 0), slots)
        self.assertNotIn(datetime(2026, 4, 13, 12, 30), slots)
        
        # Slots immediately after lunch should be available
        self.assertIn(datetime(2026, 4, 13, 13, 0), slots)
    
    def test_get_available_slots_past_time(self):
        """Test that past times are excluded for today."""
        # Set current time to 10:30 on Monday
        current_time = datetime(2026, 4, 13, 10, 30, tzinfo=timezone.get_current_timezone())
        
        monday_date = date(2026, 4, 13)  # Monday
        
        slots = AvailabilityService._get_available_slots_for_day(
            self.professional, self.service, monday_date, current_time.time()
        )
        
        # Slots before 10:30 should be blocked
        self.assertNotIn(datetime(2026, 4, 13, 9, 0), slots)
        self.assertNotIn(datetime(2026, 4, 13, 9, 30), slots)
        self.assertNotIn(datetime(2026, 4, 13, 10, 0), slots)
        
        # 10:30 and later should be available (if not on exact hour)
        # Since we use 30-minute intervals starting from hour, next would be 11:00
        self.assertIn(datetime(2026, 4, 13, 11, 0), slots)
    
    def test_get_available_slots_api_response(self):
        """Test the API response format."""
        response = AvailabilityService.get_available_slots(
            professional_id=self.professional.id,
            service_id=self.service.id,
            page=1
        )
        
        self.assertIn('results', response)
        self.assertIn('has_next', response)
        self.assertIn('has_previous', response)
        self.assertIn('current_page', response)
        
        self.assertIsInstance(response['results'], list)
        self.assertIsInstance(response['has_next'], bool)
        self.assertIsInstance(response['has_previous'], bool)
        
        if response['results']:
            result = response['results'][0]
            self.assertIn('date', result)
            self.assertIn('weekday', result)
            self.assertIn('slots', result)
            
            self.assertIsInstance(result['slots'], list)
            if result['slots']:
                self.assertIsInstance(result['slots'][0], str)
    
    def test_get_available_slots_invalid_professional(self):
        """Test with invalid professional ID."""
        response = AvailabilityService.get_available_slots(
            professional_id=999,
            service_id=self.service.id,
            page=1
        )
        
        self.assertEqual(response['results'], [])
        self.assertFalse(response['has_next'])
        self.assertFalse(response['has_previous'])
    
    def test_get_available_slots_invalid_service(self):
        """Test with invalid service ID."""
        response = AvailabilityService.get_available_slots(
            professional_id=self.professional.id,
            service_id=999,
            page=1
        )
        
        self.assertEqual(response['results'], [])
        self.assertFalse(response['has_next'])
        self.assertFalse(response['has_previous'])
    
    def test_subtract_intervals(self):
        """Test interval subtraction logic."""
        base_interval = TimeSlot(
            datetime(2026, 4, 13, 9, 0),
            datetime(2026, 4, 13, 12, 0)
        )
        
        # Single busy interval
        busy_interval = TimeSlot(
            datetime(2026, 4, 13, 10, 0),
            datetime(2026, 4, 13, 11, 0)
        )
        
        result = AvailabilityService._subtract_intervals(base_interval, [busy_interval])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].start, datetime(2026, 4, 13, 9, 0))
        self.assertEqual(result[0].end, datetime(2026, 4, 13, 10, 0))
        self.assertEqual(result[1].start, datetime(2026, 4, 13, 11, 0))
        self.assertEqual(result[1].end, datetime(2026, 4, 13, 12, 0))
    
    def test_subtract_intervals_no_overlap(self):
        """Test interval subtraction with no overlap."""
        base_interval = TimeSlot(
            datetime(2026, 4, 13, 9, 0),
            datetime(2026, 4, 13, 12, 0)
        )
        
        # Non-overlapping busy interval
        busy_interval = TimeSlot(
            datetime(2026, 4, 13, 13, 0),
            datetime(2026, 4, 13, 14, 0)
        )
        
        result = AvailabilityService._subtract_intervals(base_interval, [busy_interval])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].start, base_interval.start)
        self.assertEqual(result[0].end, base_interval.end)
    
    def test_generate_slots_from_interval(self):
        """Test slot generation from interval."""
        interval = TimeSlot(
            datetime(2026, 4, 13, 9, 0),
            datetime(2026, 4, 13, 11, 0)
        )
        
        # 30-minute service
        slots = AvailabilityService._generate_slots_from_interval(interval, 30)
        
        expected_slots = [
            datetime(2026, 4, 13, 9, 0),
            datetime(2026, 4, 13, 9, 30),
            datetime(2026, 4, 13, 10, 0),
            datetime(2026, 4, 13, 10, 30),
        ]
        
        self.assertEqual(len(slots), len(expected_slots))
        for expected in expected_slots:
            self.assertIn(expected, slots)
    
    def test_generate_slots_from_interval_service_too_long(self):
        """Test slot generation when service is too long for interval."""
        interval = TimeSlot(
            datetime(2026, 4, 13, 9, 0),
            datetime(2026, 4, 13, 9, 30)
        )
        
        # 60-minute service won't fit
        slots = AvailabilityService._generate_slots_from_interval(interval, 60)
        
        self.assertEqual(len(slots), 0)
    
    def test_clear_availability_cache(self):
        """Test cache clearing functionality."""
        # First, populate cache
        AvailabilityService.get_available_slots(
            professional_id=self.professional.id,
            service_id=self.service.id,
            page=1
        )
        
        # Verify cache exists
        cache_key = f"availability_{self.professional.id}_{self.service.id}_1"
        self.assertIsNotNone(cache.get(cache_key))
        
        # Clear cache
        AvailabilityService.clear_availability_cache(
            professional_id=self.professional.id,
            service_id=self.service.id
        )
        
        # Verify cache is cleared
        self.assertIsNone(cache.get(cache_key))
    
    def test_has_availability_after(self):
        """Test checking availability after a given date."""
        # Create schedule for multiple days
        for weekday in [0, 1, 2]:  # Monday, Tuesday, Wednesday
            ProfessionalSchedule.objects.create(
                profissional=self.professional,
                weekday=weekday,
                start_time=time(9, 0),
                end_time=time(18, 0),
                lunch_start=time(12, 0),
                lunch_end=time(13, 0)
            )
        
        check_date = date(2026, 4, 13)  # Monday
        has_availability = AvailabilityService._has_availability_after(
            self.professional, self.service, check_date
        )
        
        self.assertTrue(has_availability)


class ProfessionalScheduleTests(TestCase):
    """Test the ProfessionalSchedule model."""
    
    def setUp(self):
        """Set up test data."""
        self.professional = Profissional.objects.create(
            nome="Test Professional",
            ativo=True
        )
    
    def test_schedule_creation(self):
        """Test creating a valid schedule."""
        schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            lunch_start=time(12, 0),
            lunch_end=time(13, 0)
        )
        
        self.assertEqual(schedule.profissional, self.professional)
        self.assertEqual(schedule.weekday, ProfessionalSchedule.Weekday.MONDAY)
        self.assertEqual(schedule.start_time, time(9, 0))
        self.assertEqual(schedule.end_time, time(18, 0))
        self.assertEqual(schedule.lunch_start, time(12, 0))
        self.assertEqual(schedule.lunch_end, time(13, 0))
        self.assertFalse(schedule.is_day_off)
    
    def test_schedule_day_off(self):
        """Test creating a day off schedule."""
        schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.SUNDAY,
            is_day_off=True
        )
        
        self.assertTrue(schedule.is_day_off)
        self.assertIsNone(schedule.start_time)
        self.assertIsNone(schedule.end_time)
        self.assertIsNone(schedule.lunch_start)
        self.assertIsNone(schedule.lunch_end)
    
    def test_schedule_validation_start_after_end(self):
        """Test validation when start time is after end time."""
        with self.assertRaises(Exception):  # Should raise ValidationError
            ProfessionalSchedule.objects.create(
                profissional=self.professional,
                weekday=ProfessionalSchedule.Weekday.MONDAY,
                start_time=time(18, 0),
                end_time=time(9, 0)
            )
    
    def test_schedule_validation_invalid_lunch(self):
        """Test validation for invalid lunch break."""
        # Lunch outside working hours
        with self.assertRaises(Exception):  # Should raise ValidationError
            ProfessionalSchedule.objects.create(
                profissional=self.professional,
                weekday=ProfessionalSchedule.Weekday.MONDAY,
                start_time=time(9, 0),
                end_time=time(18, 0),
                lunch_start=time(19, 0),
                lunch_end=time(20, 0)
            )
    
    def test_schedule_unique_constraint(self):
        """Test unique constraint on professional and weekday."""
        ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        
        with self.assertRaises(Exception):  # Should raise IntegrityError
            ProfessionalSchedule.objects.create(
                profissional=self.professional,
                weekday=ProfessionalSchedule.Weekday.MONDAY,
                start_time=time(10, 0),
                end_time=time(19, 0)  # Added equals sign here
            )
    
    def test_schedule_str_representation(self):
        """Test string representation of schedule."""
        schedule = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        
        expected = f"{self.professional.nome} - Segunda-feira (09:00:00 - 18:00:00)"
        self.assertEqual(str(schedule), expected)
        
        # Test day off representation
        day_off = ProfessionalSchedule.objects.create(
            profissional=self.professional,
            weekday=ProfessionalSchedule.Weekday.SUNDAY,
            is_day_off=True
        )
        
        expected_day_off = f"{self.professional.nome} - Domingo (Folga)"
        self.assertEqual(str(day_off), expected_day_off)