# config/settings/base.py

from pathlib import Path
from decouple import config

import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'usuarios',
    'almacen',
    'compras',
    'caja',
    'ventas',
    'facturacion',
    'empresa',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-py'
TIME_ZONE = 'America/Asuncion'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Agrega esto al final de settings.py
SIFEN_CERT_PATH = os.path.join(BASE_DIR, 'sifen_certs', 'cert.pem')
SIFEN_KEY_PATH = os.path.join(BASE_DIR, 'sifen_certs', 'key.pem')

WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'facturacion': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    },
}



# Configuración común para todos los entornos
SIFEN_CONFIG = {
    'API_TIMEOUT': 30,  # Tiempo máximo de espera en segundos
    'MAX_REINTENTOS': 3,  # Número máximo de reintentos
    'TIEMPO_ENTRE_REINTENTOS': 5,  # Segundos entre reintentos
    'LOG_LEVEL': 'INFO',  # Nivel de logging
    
    # Plantillas para documentos
    'TEMPLATES': {
        'FACTURA': 'facturacion/templates/factura.xml',
        'KUDE': 'facturacion/templates/kude.html',
    },
    
    # Certificados digitales (se sobreescriben en producción)
    'CERTIFICADO': None,
    'CERTIFICADO_PASSWORD': None,
}