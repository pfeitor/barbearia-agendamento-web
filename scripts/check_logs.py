import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django; django.setup()

from apps.notificacoes.models import NotificacaoLog
logs = NotificacaoLog.objects.all().order_by("-enviado_em")
print(f"Total de logs: {logs.count()}")
print()
for l in logs:
    print(f"  [{l.status}] {l.tipo}")
    print(f"    -> {l.destinatario}")
    print(f"    Enviado em: {l.enviado_em}")
    print(f"    Agendamento: #{l.agendamento_id}")
    if l.erro:
        print(f"    ERRO: {l.erro}")
    print()
