# Availability System Documentation

## Overview

This document describes the complete availability-based scheduling system implemented for the barber shop application. The system provides real-time availability calculation based on professional schedules, existing appointments, and service durations.

## Features

### 1. Professional Schedules
- **Weekly schedule management** with working hours and lunch breaks
- **Day off support** for non-working days
- **Validation** to ensure logical time constraints
- **Unique constraints** to prevent duplicate schedules

### 2. Real-time Availability Calculation
- **Dynamic slot generation** based on service duration
- **Conflict detection** with existing appointments
- **Lunch break exclusion** from available slots
- **Past time filtering** for same-day bookings
- **30-minute interval grid** for consistent scheduling

### 3. API Endpoint
- **RESTful API** for availability data
- **Pagination support** for multiple days
- **JSON response format** with structured data
- **Error handling** for invalid parameters

### 4. Enhanced UI
- **Dynamic time slot selection** using JavaScript
- **Real-time updates** when professional/service changes
- **Pagination controls** for browsing available days
- **Visual feedback** for loading states and errors

## Database Schema

### ProfessionalSchedule Model

```python
class ProfessionalSchedule(models.Model):
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=Weekday.choices)  # 0-6 (Mon-Sun)
    start_time = models.TimeField()
    end_time = models.TimeField()
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)
    is_day_off = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Features:**
- Unique constraint on `(profissional, weekday)`
- Proper time validation in `clean()` method
- Automatic clearing of time fields for day off

## API Endpoints

### GET /agendamentos/availability/

**Query Parameters:**
- `professional_id` (required): ID of the professional
- `service_id` (required): ID of the service
- `page` (optional): Page number for pagination (default: 1)

**Response Format:**
```json
{
  "results": [
    {
      "date": "2026-04-13",
      "weekday": "Monday",
      "slots": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]
    }
  ],
  "has_next": true,
  "has_previous": false,
  "current_page": 1
}
```

## Availability Algorithm

### Core Logic

1. **Get Professional Schedule**: Retrieve schedule for the specific weekday
2. **Check Day Off**: Skip if it's a day off
3. **Calculate Working Hours**: Create base interval from start_time to end_time
4. **Get Busy Intervals**: Fetch existing appointments for the day
5. **Add Lunch Break**: Create lunch interval if configured
6. **Subtract Busy Times**: Remove appointments and lunch from working hours
7. **Generate Valid Slots**: Create 30-minute slots that fit service duration
8. **Filter Past Times**: Exclude slots that have already passed for today

### TimeSlot Class

Utility class for time interval operations:

```python
class TimeSlot:
    def __init__(self, start: datetime, end: datetime)
    def duration_minutes(self) -> int
    def can_fit_service(self, duration_minutes: int) -> bool
    def overlaps_with(self, other: 'TimeSlot') -> bool
```

## Frontend Integration

### Enhanced Template

The `form_enhanced.html` template provides:

1. **Dynamic Loading**: Fetches availability via AJAX when professional/service selected
2. **Slot Selection**: Interactive time slot buttons with visual feedback
3. **Pagination**: Navigate through multiple days of availability
4. **Error Handling**: User-friendly error messages and loading states

### JavaScript Features

- Real-time API calls to availability endpoint
- Dynamic DOM manipulation for slots
- Form validation before submission
- Pagination controls
- Loading state management

## Caching Strategy

### Cache Keys
- Format: `availability_{professional_id}_{service_id}_{page}`
- TTL: 5 minutes (300 seconds)

### Cache Invalidation
- Automatic clearing on appointment creation/update/deletion
- Manual clearing via `AvailabilityService.clear_availability_cache()`

## Testing

### Unit Tests Coverage

1. **TimeSlot Tests**: Basic utility functionality
2. **AvailabilityService Tests**: Core availability calculation
3. **ProfessionalSchedule Tests**: Model validation and constraints

### Test Scenarios

- Basic availability calculation
- Appointment conflict detection
- Lunch break exclusion
- Past time filtering
- Edge cases (no schedule, day off, etc.)
- API response format validation
- Cache functionality

## Migration Strategy

### Production Database

The system includes a migration file that:
1. Creates the `ProfessionalSchedule` table
2. Adds proper indexes for performance
3. Sets up unique constraints
4. Is safe to run on existing databases

### Data Migration

After running migrations, you'll need to:
1. Create professional schedules for existing professionals
2. Use the provided setup script for sample data
3. Update any existing appointment logic

## Performance Considerations

### Database Optimization

1. **Indexes**: Proper indexes on professional, weekday, and datetime fields
2. **Query Optimization**: Uses `select_related()` to reduce N+1 queries
3. **Efficient Filtering**: Filters appointments by date and status

### Caching

1. **Response Caching**: 5-minute cache for availability responses
2. **Smart Invalidation**: Clears cache only when relevant data changes
3. **Cache Keys**: Structured keys for easy management

## Usage Examples

### Setting up Sample Data

```bash
python manage.py shell < scripts/setup_availability_data.py
```

### Testing API Endpoint

```bash
# Get availability for professional 1, service 1
curl "http://localhost:8000/agendamentos/availability/?professional_id=1&service_id=1"

# Get page 2
curl "http://localhost:8000/agendamentos/availability/?professional_id=1&service_id=1&page=2"
```

### Creating Professional Schedule

```python
from apps.profissionais.models import Profissional, ProfessionalSchedule
from datetime import time

professional = Profissional.objects.get(id=1)

# Monday schedule with lunch
schedule = ProfessionalSchedule.objects.create(
    profissional=professional,
    weekday=ProfessionalSchedule.Weekday.MONDAY,
    start_time=time(9, 0),
    end_time=time(18, 0),
    lunch_start=time(12, 0),
    lunch_end=time(13, 0)
)

# Sunday off
day_off = ProfessionalSchedule.objects.create(
    profissional=professional,
    weekday=ProfessionalSchedule.Weekday.SUNDAY,
    is_day_off=True
)
```

## Error Handling

### Common Issues

1. **No Schedule Found**: Returns empty results array
2. **Invalid Parameters**: Returns 400 error with message
3. **Service Too Long**: No slots generated if service doesn't fit
4. **Past Date**: Empty results for dates before today

### Error Responses

```json
{
  "error": "professional_id and service_id are required",
  "results": [],
  "has_next": false,
  "has_previous": false
}
```

## Future Enhancements

### Planned Features

1. **Custom Exceptions**: Handle special days, holidays, etc.
2. **Multiple Lunch Breaks**: Support for multiple break periods
3. **Flexible Intervals**: Configurable time slot intervals
4. **Recurring Exceptions**: Regular maintenance periods, etc.
5. **Advanced Filtering**: By service type, professional specialty, etc.

### Scalability Considerations

1. **Redis Integration**: For better caching performance
2. **Background Jobs**: For pre-computing availability
3. **Database Sharding**: For high-volume scenarios
4. **API Rate Limiting**: To prevent abuse

## Troubleshooting

### Common Problems

1. **No Availability Showing**
   - Check professional schedules exist
   - Verify service duration is reasonable
   - Check for conflicting appointments

2. **Performance Issues**
   - Ensure database indexes are created
   - Check cache configuration
   - Monitor query performance

3. **Frontend Issues**
   - Verify JavaScript console for errors
   - Check API endpoint responses
   - Ensure proper CSRF tokens

## Security Considerations

1. **Access Control**: API endpoints respect user permissions
2. **Data Validation**: All inputs properly validated
3. **CSRF Protection**: Forms include proper CSRF tokens
4. **SQL Injection Prevention**: Uses Django ORM properly

## Support

For issues or questions about the availability system:

1. Check the test files for usage examples
2. Review the API documentation above
3. Check browser console for frontend issues
4. Verify Django logs for backend errors
