import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Cliente, ClienteUser


def _validar_senha_forte(senha):
    """Valida: mínimo 8 chars (aplicado pelo widget min_length), 1 maiúscula, 1 número."""
    if not re.search(r'[A-Z]', senha):
        raise ValidationError('A senha deve conter ao menos 1 letra maiúscula.')
    if not re.search(r'\d', senha):
        raise ValidationError('A senha deve conter ao menos 1 número.')


class ClienteRegistroForm(forms.Form):
    nome = forms.CharField(
        max_length=100,
        label='Nome completo',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome'}),
    )
    telefone = forms.CharField(
        max_length=20,
        label='Telefone',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'voce@email.com'}),
    )
    senha = forms.CharField(
        min_length=8,
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    confirmar_senha = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if ClienteUser.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean_telefone(self):
        telefone = self.cleaned_data['telefone']
        if Cliente.objects.filter(telefone=telefone).exists():
            raise ValidationError('Este telefone já está cadastrado.')
        return telefone

    def clean_senha(self):
        senha = self.cleaned_data.get('senha', '')
        _validar_senha_forte(senha)
        return senha

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        confirmar = cleaned.get('confirmar_senha')
        if senha and confirmar and senha != confirmar:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        return cleaned


class VerificacaoEmailForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        label='Código de verificação',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
        }),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if not codigo.isdigit():
            raise ValidationError('O código deve conter apenas números.')
        return codigo


class ClienteLoginEmailForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'voce@email.com'}),
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )


class EsqueciSenhaForm(forms.Form):
    email = forms.EmailField(
        label='E-mail cadastrado',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'voce@email.com'}),
    )


class NovaSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        min_length=8,
        label='Nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    confirmar_senha = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_nova_senha(self):
        senha = self.cleaned_data.get('nova_senha', '')
        _validar_senha_forte(senha)
        return senha

    def clean(self):
        cleaned = super().clean()
        nova = cleaned.get('nova_senha')
        confirmar = cleaned.get('confirmar_senha')
        if nova and confirmar and nova != confirmar:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        return cleaned


class ClienteForm(forms.ModelForm):
    """Edição de dados do perfil — usado por admin (CRUD) e ClienteMeusDadosView."""

    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
