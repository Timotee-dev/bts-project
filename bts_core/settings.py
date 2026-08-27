"""
BTS Project — Production-Ready Django Settings
Supports: SQLite (dev) → PostgreSQL/Supabase (prod/Render)
Static files: WhiteNoise
"""

from pathlib import Path
from decouple import config, Csv
import urllib.parse
import cloudinary

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)

# ─── Apps ────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'store',
    'accounts',
    'vendors',
    'cloudinary',
    'cloudinary_storage',
]

# ─── Middleware ───────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bts_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.cart_count',
                'store.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'bts_core.wsgi.application'

# ─── Database ────────────────────────────────────────────────
# Local dev  → SQLite (no config needed)
# Production → set DATABASE_URL in Render environment variables
_db_url = config('DATABASE_URL', default='')

if _db_url:
    _parsed = urllib.parse.urlparse(_db_url)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _parsed.path.lstrip('/'),
            'USER': urllib.parse.unquote(_parsed.username or ''),
            'PASSWORD': urllib.parse.unquote(_parsed.password or ''),
            'HOST': _parsed.hostname,
            'PORT': _parsed.port or 5432,
            'OPTIONS': {
                'sslmode': 'require',
            },
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─── Auth ────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.Customer'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ─── Internationalisation ─────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# ─── Static Files (WhiteNoise) ───────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ─── Media Files ─────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Cloudinary ──────────────────────────────────────────────
cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUD_NAME', default=''),
    api_key=config('CLOUDINARY_API_KEY', default=''),
    api_secret=config('CLOUDINARY_API_SECRET', default=''),
)

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ─── Security Headers (production only) ──────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ─── REST Framework ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:8000',
    cast=Csv()
)

# ─── Email / Brevo ───────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 2525
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config('BREVO_SMTP_LOGIN', default='')
EMAIL_HOST_PASSWORD = config('BREVO_SMTP_KEY', default='')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')

# ─── Payments ────────────────────────────────────────────────
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')

# ─── Site URL (used in emails) ───────────────────────────────
SITE_URL = config(
    'SITE_URL',
    default='http://127.0.0.1:8000'
)

# ─── BTS App Settings ────────────────────────────────────────
BTS_MIN_CUSTOM_ITEMS = config(
    'BTS_MIN_CUSTOM_ITEMS',
    default=5,
    cast=int
)

BTS_CUSTOM_PACKAGING_FEE = config(
    'BTS_CUSTOM_PACKAGING_FEE',
    default=1500,
    cast=int
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'