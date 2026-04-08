from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from .forms import ProfissionalForm
from .models import Profissional


class ProfissionalListView(LoginRequiredMixin, ListView):
    model = Profissional
    template_name = "profissionais/lista.html"
    context_object_name = "profissionais"


class ProfissionalCreateView(LoginRequiredMixin, CreateView):
    model = Profissional
    form_class = ProfissionalForm
    template_name = "profissionais/form.html"
    success_url = reverse_lazy("profissionais_lista")

    def form_valid(self, form):
        messages.success(self.request, "Profissional criado com sucesso.")
        return super().form_valid(form)


class ProfissionalUpdateView(LoginRequiredMixin, UpdateView):
    model = Profissional
    form_class = ProfissionalForm
    template_name = "profissionais/form.html"
    success_url = reverse_lazy("profissionais_lista")

    def form_valid(self, form):
        messages.success(self.request, "Profissional atualizado com sucesso.")
        return super().form_valid(form)


class ProfissionalDeleteView(LoginRequiredMixin, DeleteView):
    model = Profissional
    template_name = "profissionais/confirm_delete.html"
    success_url = reverse_lazy("profissionais_lista")

    def form_valid(self, form):
        messages.success(self.request, "Profissional removido com sucesso.")
        return super().form_valid(form)
