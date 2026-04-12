from django import forms


class ClienteLoginForm(forms.Form):
    """Formulário de login para cliente por telefone."""
    telefone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu telefone',
            'autocomplete': 'tel'
        })
    )


class AdminLoginForm(forms.Form):
    """Formulário de login para administrador por email e senha."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu email',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha',
            'autocomplete': 'current-password'
        })
    )
