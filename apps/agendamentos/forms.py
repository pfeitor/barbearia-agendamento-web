from django import forms
from .models import Agendamento


class AgendamentoForm(forms.ModelForm):
    data_hora_inicio = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    def __init__(self, *args, **kwargs):
        user_cliente = kwargs.pop('user_cliente', None)
        super().__init__(*args, **kwargs)
        
        # Se for cliente logado, filtra o campo cliente para mostrar apenas ele mesmo
        if user_cliente:
            self.fields['cliente'].queryset = self.fields['cliente'].queryset.filter(id=user_cliente.id)
            self.fields['cliente'].initial = user_cliente
            self.fields['cliente'].widget = forms.HiddenInput()  # Esconde o campo para cliente
            # Remove campos que cliente não deve ver/editar
            for field in ['status', 'confirmado_whatsapp']:
                if field in self.fields:
                    del self.fields[field]

    class Meta:
        model = Agendamento
        fields = ["data_hora_inicio", "status", "confirmado_whatsapp", "cliente", "profissional", "servico"]
