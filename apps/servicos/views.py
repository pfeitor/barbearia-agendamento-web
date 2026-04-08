from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from .forms import ServicoForm
from .models import Servico


class ServicoListView(LoginRequiredMixin, ListView):
    model = Servico
    template_name = "servicos/lista.html"
    context_object_name = "servicos"


class ServicoCreateView(LoginRequiredMixin, CreateView):
    model = Servico
    form_class = ServicoForm
    template_name = "servicos/form.html"
    success_url = reverse_lazy("servicos_lista")

    def form_valid(self, form):
        messages.success(self.request, "Serviço criado com sucesso.")
        return super().form_valid(form)


class ServicoUpdateView(LoginRequiredMixin, UpdateView):
    model = Servico
    form_class = ServicoForm
    template_name = "servicos/form.html"
    success_url = reverse_lazy("servicos_lista")

    def form_valid(self, form):
        messages.success(self.request, "Serviço atualizado com sucesso.")
        return super().form_valid(form)


class ServicoDeleteView(LoginRequiredMixin, DeleteView):
    model = Servico
    template_name = "servicos/confirm_delete.html"
    success_url = reverse_lazy("servicos_lista")

    def form_valid(self, form):
        messages.success(self.request, "Serviço removido com sucesso.")
        return super().form_valid(form)
