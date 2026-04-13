from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Profissional(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "profissional"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class ProfessionalSchedule(models.Model):
    """Manage professional weekly availability with working hours and lunch breaks."""
    
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Segunda-feira"
        TUESDAY = 1, "Terça-feira"
        WEDNESDAY = 2, "Quarta-feira"
        THURSDAY = 3, "Quinta-feira"
        FRIDAY = 4, "Sexta-feira"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    profissional = models.ForeignKey(
        Profissional, 
        on_delete=models.CASCADE, 
        related_name="schedules"
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)
    is_day_off = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "professional_schedule"
        ordering = ["weekday", "start_time"]
        unique_together = ["profissional", "weekday"]
        indexes = [
            models.Index(fields=["profissional", "weekday"]),
        ]

    def __str__(self):
        weekday_name = self.Weekday(self.weekday).label
        if self.is_day_off:
            return f"{self.profissional.nome} - {weekday_name} (Folga)"
        return f"{self.profissional.nome} - {weekday_name} ({self.start_time} - {self.end_time})"

    def clean(self):
        """Validate time logic."""
        if self.is_day_off:
            # If day off, clear time fields
            self.start_time = None
            self.end_time = None
            self.lunch_start = None
            self.lunch_end = None
            return

        if not self.start_time or not self.end_time:
            raise ValidationError("Horários de início e fim são obrigatórios em dias de trabalho.")

        if self.start_time >= self.end_time:
            raise ValidationError("Horário de início deve ser anterior ao horário de fim.")

        # Validate lunch break if provided
        if self.lunch_start and self.lunch_end:
            if self.lunch_start >= self.lunch_end:
                raise ValidationError("Horário de início do almoço deve ser anterior ao horário de fim.")
            
            if not (self.start_time < self.lunch_start < self.end_time):
                raise ValidationError("Almoço deve estar dentro do horário de trabalho.")
            
            if not (self.start_time < self.lunch_end < self.end_time):
                raise ValidationError("Fim do almoço deve estar dentro do horário de trabalho.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
