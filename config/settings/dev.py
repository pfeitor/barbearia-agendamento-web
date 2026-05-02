from .base import *

DEBUG = True

# Em desenvolvimento: sem EMAIL_HOST_PASSWORD → imprime e-mails no terminal
from decouple import config as _config
if not _config("EMAIL_HOST_PASSWORD", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
