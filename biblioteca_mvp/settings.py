import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variaveis do .env (gitignored) ANTES de ler qualquer chave
load_dotenv(BASE_DIR / '.env')

# SECRET_KEY: lida do .env. O fallback existe apenas para desenvolvimento local;
# em qualquer ambiente compartilhado, defina DJANGO_SECRET_KEY no .env.
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-biblioteca-mvp-dev-only-change-in-production-abc456',
)

# DEBUG: desligado por padrão. Ative com DJANGO_DEBUG=true no .env (dev).
DEBUG = os.getenv('DJANGO_DEBUG', 'False').strip().lower() in ('1', 'true', 'yes', 'on')

# ALLOWED_HOSTS: lista separada por vírgula no .env. Em DEBUG aceita localhost por padrão.
_allowed = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').strip()
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'recomendador',
    'metricas',
    'bootstrap5',
    'django_tables2',
]

RECOMENDADOR_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
RECOMENDADOR_MOCK = False  # True = gera embeddings aleatorios (para CI / sem rede)

# Chat RAG — lidos do .env via python-dotenv (ver biblioteca_mvp/.env)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

ROOT_URLCONF = 'biblioteca_mvp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'biblioteca_mvp.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/menu/'
