from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(override=False)

def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

DEBUG = os.environ.get("DEBUG", "False") == "True"

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-123456")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".up.railway.app",
]
ALLOWED_HOSTS += [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop.apps.ShopConfig",
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

ROOT_URLCONF = "myshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.telegram_user",
            ],
        },
    },
]

WSGI_APPLICATION = "myshop.wsgi.application"

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.parse(os.environ.get("DATABASE_URL"))

if not DEBUG and not os.environ.get("DATABASE_URL"):
    db_defaults = DATABASES["default"]
    missing_db_fields = [
        key for key, value in db_defaults.items()
        if key in {"NAME", "USER", "PASSWORD", "HOST", "PORT"} and not value
    ]
    if missing_db_fields:
        raise ValueError(
            "Database settings missing: " + ", ".join(sorted(missing_db_fields))
        )

PASSWORD_VALIDATORS_ENABLED = env_bool("PASSWORD_VALIDATORS_ENABLED", not DEBUG)
if PASSWORD_VALIDATORS_ENABLED:
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]
else:
    AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static"
]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "daqsvvw0g")
VK_APP_ID = os.environ.get('VK_APP_ID', '54499010')

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")



# Если нужно полностью отключить X-Frame-Options для определённых views:
# В shop/views.py для miniapp добавь декоратор:
# from django.views.decorators.clickjacking import xframe_options_exempt
# @xframe_options_exempt
# def miniapp(request):
#     ...

# Разрешаем VK загружать приложение в iframe
X_FRAME_OPTIONS = 'ALLOWALL'

# Добавляем VK в доверенные источники
CSRF_TRUSTED_ORIGINS = [
    'https://myshop-production-2acb.up.railway.app',
    'https://web.telegram.org',
    'https://t.me',
    'https://telegram.org',
    'https://vk.com',
    'https://m.vk.com',
    'https://*.vk.com',
]

# Для продакшена лучше использовать конкретные домены
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
