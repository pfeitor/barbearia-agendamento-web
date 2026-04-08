from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from .forms import AgendamentoForm
from .models import Agendamento


class AgendamentoListView(LoginRequiredMixin, ListView):
    model = Agendamento
    template_name = "agendamentos/lista.html"
    context_object_name = "agendamentos"


class AgendamentoCreateView(LoginRequiredMixin, CreateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = "agendamentos/form.html"
    success_url = reverse_lazy("agendamentos_lista")

    def form_valid(self, form):
        messages.success(self.request, "Agendamento criado com sucesso.")
        return super().form_valid(form)


class AgendamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Agendamento
    form_class = AgendamentoForm
    template_name = "agendamentos/form.html"
    success_url = reverse_lazy("agendamentos_lista")

    def form_valid(self, form):
        messages.success(self.request, "Agendamento atualizado com sucesso.")
        return super().form_valid(form)


class AgendamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Agendamento
    template_name = "agendamentos/confirm_delete.html"
    success_url = reverse_lazy("agendamentos_lista")

    def form_valid(self, form):
        messages.success(self.request, "Agendamento removido com sucesso.")
        return super().form_valid(form)
