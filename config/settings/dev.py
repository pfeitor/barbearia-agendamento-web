from .base import *

DEBUG = True

# Em desenvolvimento: sem senha SMTP ou sem chave Brevo -> imprime e-mails no terminal.
from decouple import config as _config

if (
    EMAIL_PROVIDER == "smtp"
    and not _config("SMTP_EMAIL_HOST_PASSWORD", default=_config("EMAIL_HOST_PASSWORD", default=""))
) or (
    EMAIL_PROVIDER == "brevo"
    and not API_KEY_BREVO
):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
