from .base import *

DEBUG = True

# Em desenvolvimento:
# - Se EMAIL_HOST_PASSWORD estiver configurado no .env → usa SMTP real (Gmail)
# - Caso contrário → exibe e-mails no terminal (sem precisar de credenciais)
from decouple import config as _config
if not _config("EMAIL_HOST_PASSWORD", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
