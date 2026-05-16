from pathlib import Path
import os
import dj_database_url
from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]
TIME_ZONE = os.getenv("TIME_ZONE", "America/Sao_Paulo")
IS_PRODUCTION_SETTINGS = os.getenv("DJANGO_SETTINGS_MODULE", "").endswith(".prod")
IS_RENDER_RUNTIME = os.getenv("RENDER_SERVICE_TYPE") == "web" and not os.getenv("RENDER_BUILD_ID")

# Deve ser declarado antes de qualquer model que referencie o usuário
AUTH_USER_MODEL = 'clientes.ClienteUser'

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

# Usar SQLite durante build do Render. Fora disso, DATABASE_URL tem prioridade.
DATABASE_URL = config("DATABASE_URL", default="")
if os.getenv("RENDER_BUILD_ID"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=config(
                "DATABASE_SSL_REQUIRE",
                default=IS_PRODUCTION_SETTINGS or IS_RENDER_RUNTIME,
                cast=bool,
            ),
        )
    }
else:
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

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    'apps.core.backends.AdminEmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = "/clientes/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/clientes/login/"

PASSWORD_RESET_TIMEOUT = 3600  # tokens de reset expiram em 1 hora

HANDLER403 = 'apps.core.views.permission_denied'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# E-mail transacional
EMAIL_PROVIDER = config("EMAIL_PROVIDER", default="smtp").strip().lower()
if EMAIL_PROVIDER not in {"smtp", "brevo"}:
    raise ImproperlyConfigured("EMAIL_PROVIDER deve ser 'smtp' ou 'brevo'.")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=465, cast=int)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=True, cast=bool)
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=10, cast=int)

# Fallback temporario para nao quebrar ambientes ainda usando os nomes antigos.
EMAIL_HOST_USER = config(
    "SMTP_EMAIL_HOST_USER",
    default=config("EMAIL_HOST_USER", default=""),
)
EMAIL_HOST_PASSWORD = config(
    "SMTP_EMAIL_HOST_PASSWORD",
    default=config("EMAIL_HOST_PASSWORD", default=""),
)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)

API_KEY_BREVO = config("API_KEY_BREVO", default="")
BREVO_SENDER_NAME = config("BREVO_SENDER_NAME", default="")
BREVO_SENDER_EMAIL = config("BREVO_SENDER_EMAIL", default="")
BREVO_TIMEOUT = config("BREVO_TIMEOUT", default=10, cast=int)

if EMAIL_PROVIDER == "brevo" and (IS_PRODUCTION_SETTINGS or IS_RENDER_RUNTIME):
    missing_brevo = [
        name
        for name, value in {
            "API_KEY_BREVO": API_KEY_BREVO,
            "BREVO_SENDER_NAME": BREVO_SENDER_NAME,
            "BREVO_SENDER_EMAIL": BREVO_SENDER_EMAIL,
        }.items()
        if not value
    ]
    if missing_brevo:
        raise ImproperlyConfigured(
            "EMAIL_PROVIDER=brevo requer as variaveis: "
            + ", ".join(missing_brevo)
            + "."
        )

BARBEARIA_NOME = config("BARBEARIA_NOME", default="Barbearia")

# ─── Feature 02: confirmação de agendamento por link ──────────────────────────
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")
LEMBRETE_DIAS_ANTECEDENCIA = [
    int(d) for d in config("LEMBRETE_DIAS_ANTECEDENCIA", default="3,1,0").split(",")
]
