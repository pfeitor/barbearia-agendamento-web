from .base import *

DEBUG = True

# Em desenvolvimento, e-mails são exibidos no terminal (sem precisar de Gmail)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
