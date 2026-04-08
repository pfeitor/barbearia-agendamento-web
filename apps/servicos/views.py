from django.http import HttpResponse


def lista_servicos(request):
    return HttpResponse("Lista de serviços")
