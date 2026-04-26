from pathlib import Path
import os
import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]
TIME_ZONE = os.getenv("TIME_ZONE", "America/Sao_Paulo")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.clientes",
    "apps.profissionais",
    "apps.servicos",
    "apps.agendamentos",
    "apps.notificacoes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Usar SQLite durante build, PostgreSQL em produção
if os.getenv("RENDER_SERVICE_TYPE") == "web" and not os.getenv("RENDER_BUILD_ID"):
    # Em produção (deploy rodando)
    DATABASES = {
        "default": dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
            ssl_require=True,
            engine='django.db.backends.postgresql',
        )
    }
else:
    # Durante build ou local
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LANGUAGE_CODE = "pt-br"
USE_I18N = True
USE_TZ = True
TIME_ZONE = TIME_ZONE
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Configurações de autenticação
AUTHENTICATION_BACKENDS = [
    'apps.core.backends.AdminEmailBackend',
    'django.contrib.auth.backends.ModelBackend',  # Para Django Admin
]

# URLs de redirecionamento
LOGIN_URL = "/login-cliente/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login-cliente/"

# Handler para 403
HANDLER403 = 'apps.core.views.permission_denied'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── E-mail (Gmail SMTP) ───────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
BARBEARIA_NOME = config("BARBEARIA_NOME", default="Barbearia")
