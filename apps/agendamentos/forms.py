from django import forms
from .models import Agendamento


class AgendamentoForm(forms.ModelForm):
    data_hora_inicio = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    class Meta:
        model = Agendamento
        fields = ["data_hora_inicio", "status", "confirmado_whatsapp", "cliente", "profissional", "servico"]
