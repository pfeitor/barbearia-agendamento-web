"""Script de teste de envio de e-mail — executar apenas uma vez."""

import os
import sys
import django

# Garante que a raiz do projeto está no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.core.mail import EmailMultiAlternatives  # noqa: E402
from django.conf import settings  # noqa: E402

subject = "✅ Teste — Sistema de Notificações PI Barbearia"

text_body = (
    "Olá!\n\n"
    "Este e-mail é um teste do sistema de notificações da PI Barbearia.\n\n"
    "Se você recebeu esta mensagem, o envio via Gmail SMTP está funcionando corretamente!\n\n"
    "-- Sistema PI Barbearia\n"
)

html_body = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="background:#f4f4f5;font-family:Arial,sans-serif;padding:32px;">
  <div style="max-width:500px;margin:auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08);">
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px;text-align:center;">
      <h1 style="color:#f0c040;margin:0;font-size:22px;">✂️ PI Barbearia</h1>
      <p style="color:#a0a0b8;margin:8px 0 0;font-size:14px;">Sistema de Agendamento Online</p>
    </div>
    <div style="padding:32px;">
      <h2 style="color:#1a1a2e;font-size:18px;margin-bottom:12px;">✅ Teste de Notificação</h2>
      <p style="color:#555;line-height:1.6;margin-bottom:16px;">
        Este e-mail é um <strong>teste do sistema de notificações</strong> da <strong>PI Barbearia</strong>.
      </p>
      <p style="color:#22c55e;font-weight:bold;font-size:15px;">
        Se você recebeu esta mensagem, o envio via Gmail SMTP está funcionando corretamente!
      </p>
      <hr style="margin:24px 0;border:none;border-top:1px solid #eee;">
      <p style="color:#888;font-size:12px;margin:0;">
        Configurações usadas:<br>
        <code>EMAIL_HOST: smtp.gmail.com:587 (TLS)</code><br>
        <code>FROM: {from_email}</code>
      </p>
    </div>
  </div>
</body>
</html>""".format(from_email=settings.DEFAULT_FROM_EMAIL)

msg = EmailMultiAlternatives(
    subject=subject,
    body=text_body,
    from_email=settings.DEFAULT_FROM_EMAIL,
    to=["paulo_feitor@yahoo.com.br"],
    cc=["pibarbeariaagendamentos@gmail.com"],
)
msg.attach_alternative(html_body, "text/html")

print(f"Enviando e-mail de teste...")
print(f"  De:   {settings.DEFAULT_FROM_EMAIL}")
print(f"  Para: paulo_feitor@yahoo.com.br")
print(f"  CC:   pibarbeariaagendamentos@gmail.com")
print(f"  SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print()

msg.send(fail_silently=False)
print("[OK] E-mail enviado com sucesso!")
