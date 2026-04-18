# Como Funciona o Fluxo de Telas/Templates no Django

## 1. Estrutura Básica do Fluxo Django

```
URL Request → View → Template → Response
```

## 2. Exemplo Prático: Sistema de Agendamentos

### 2.1. Configuração das URLs (`config/urls.py`)

```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('agendamentos/', include('apps.agendamentos.urls')),
    # ... outros apps
]
```

### 2.2. URLs do App (`apps/agendamentos/urls.py`)

```python
urlpatterns = [
    # URLs administrativas
    path("", AgendamentoListView.as_view(), name="agendamentos_lista"),
    path("novo/", AgendamentoCreateView.as_view(), name="agendamentos_create"),
    path("<int:pk>/editar/", AgendamentoUpdateView.as_view(), name="agendamentos_editar"),
    path("<int:pk>/excluir/", AgendamentoDeleteView.as_view(), name="agendamentos_excluir"),
    
    # URLs do cliente
    path("meus-agendamentos/", MeusAgendamentosView.as_view(), name="meus_agendamentos"),
    
    # API endpoints
    path("availability/", availability_api_view, name="availability_api"),
    path("simple-final-availability/", simple_final_availability, name="simple_final_availability"),
]
```

## 3. Fluxo Detalhado de Requisição

### 3.1. Exemplo: Acessar Lista de Agendamentos

**1. Requisição do Usuário:**
```
GET /agendamentos/
```

**2. Roteamento (`config/urls.py`):**
- Encontra `path('agendamentos/', include('apps.agendamentos.urls'))`
- Repassa para `apps/agendamentos/urls.py`

**3. Roteamento do App (`apps/agendamentos/urls.py`):**
- Encontra `path("", AgendamentoListView.as_view(), name="agendamentos_lista")`
- Direciona para `AgendamentoListView`

**4. View (`apps/agendamentos/views.py`):**
```python
class AgendamentoListView(LoginRequiredMixin, ListView):
    model = Agendamento
    template_name = "agendamentos/list.html"
    context_object_name = "agendamentos"
    paginate_by = 10
    
    def get_queryset(self):
        # Lógica de filtragem
        return Agendamento.objects.all()
```

**5. Template Rendering (`templates/agendamentos/list.html`):**
```html
{% extends "base.html" %}

{% block content %}
<div class="container">
    <h1>Lista de Agendamentos</h1>
    
    {% for agendamento in agendamentos %}
        <div class="card">
            <h3>{{ agendamento.cliente.nome }}</h3>
            <p>{{ agendamento.data_hora_inicio }}</p>
            <a href="{% url 'agendamentos_editar' agendamento.pk %}">Editar</a>
        </div>
    {% endfor %}
</div>
{% endblock %}
```

### 3.2. Exemplo: Editar Agendamento

**1. Requisição do Usuário:**
```
GET /agendamentos/5/editar/
```

**2. Roteamento:**
- `path("<int:pk>/editar/", AgendamentoUpdateView.as_view(), name="agendamentos_editar")`
- PK = 5 é passado como parâmetro

**3. View (`AgendamentoUpdateView`):**
```python
class AgendamentoUpdateView(AdminOrClienteMixin, UpdateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = "agendamentos/form_clean.html"
    
    def get_object(self):
        # Busca o agendamento com PK=5
        return Agendamento.objects.get(pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_title'] = 'Editar Agendamento'
        return context
```

**4. Form (`AgendamentoForm`):**
```python
class AgendamentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configura campos
        
    class Meta:
        model = Agendamento
        fields = ["data_hora_inicio", "cliente", "profissional", "servico"]
```

**5. Template (`form_clean.html`):**
```html
{% extends "base.html" %}

{% block content %}
<form method="post" id="agendamento-form">
    {% csrf_token %}
    
    <!-- Hidden fields -->
    {{ form.data_hora_inicio }}
    {{ form.cliente }}
    
    <!-- Visible fields -->
    {{ form.profissional }}
    {{ form.servico }}
    
    <button type="submit">Salvar</button>
</form>
{% endblock %}
```

## 4. Herança de Templates

### 4.1. Base Template (`templates/base.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Barbearia{% endblock %}</title>
</head>
<body>
    <header>
        {% include "includes/navbar.html" %}
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        {% include "includes/footer.html" %}
    </footer>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 4.2. Template Filho (`form_clean.html`)
```html
{% extends "base.html" %}  <!-- Herda do base -->

{% block title %}{{ view_title }}{% endblock %}  <!-- Sobrescreve title -->

{% block content %}  <!-- Insere conteúdo no main -->
<!-- Conteúdo do formulário -->
{% endblock %}

{% block extra_js %}  <!-- Adiciona JavaScript extra -->
<script>
// JavaScript específico do formulário
</script>
{% endblock %}
```

## 5. Sistema de Contexto

### 5.1. Contexto Global (via `context_processors`)
```python
# config/settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_info',  # Custom
            ],
        },
    },
]
```

### 5.2. Contexto da View
```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['view_title'] = 'Editar Agendamento'
    context['user_role'] = 'admin'
    return context
```

## 6. Fluxo de Formulário (POST)

### 6.1. Submit do Formulário
```
POST /agendamentos/5/editar/
```

### 6.2. View Processamento
```python
class AgendamentoUpdateView(UpdateView):
    def form_valid(self, form):
        # Dados válidos
        messages.success(self.request, "Agendamento atualizado!")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Dados inválidos
        messages.error(self.request, "Corrija os erros!")
        return super().form_invalid(form)
    
    def get_success_url(self):
        # Para onde redirecionar após sucesso
        return reverse_lazy("agendamentos_lista")
```

## 7. URLs Nomeadas e Reverse

### 7.1. Definição
```python
path("novo/", AgendamentoCreateView.as_view(), name="agendamentos_create")
```

### 7.2. Uso nos Templates
```html
<a href="{% url 'agendamentos_create' %}">Novo Agendamento</a>
<a href="{% url 'agendamentos_editar' agendamento.pk %}">Editar</a>
```

### 7.3. Uso nas Views
```python
from django.urls import reverse_lazy

def get_success_url(self):
    return reverse_lazy("agendamentos_lista")
```

## 8. Middleware Pipeline

```
Request → Middleware 1 → Middleware 2 → ... → View → Response → Middleware N → ... → Client
```

Exemplos de middleware:
- `AuthenticationMiddleware`: Adiciona `user` ao request
- `SessionMiddleware`: Gerencia sessões
- `MessageMiddleware`: Sistema de mensagens
- `CsrfViewMiddleware`: Proteção CSRF

## 9. Resumo da Ordem

1. **Requisição HTTP** chega ao servidor
2. **Middleware** processa a requisição
3. **URL Router** encontra a view correspondente
4. **View** processa a lógica:
   - Busca dados do banco
   - Processa formulários
   - Prepara contexto
5. **Template Engine** renderiza o HTML:
   - Aplica herança de templates
   - Processa tags e filtros
   - Insere dados do contexto
6. **Response** é enviada através do middleware
7. **Browser** recebe e renderiza a página

Este fluxo garante a separação de responsabilidades e permite um código organizado e manutenível.
