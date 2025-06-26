from .base import *
import os
from decouple import config

DEBUG = False

ALLOWED_HOSTS = ['django-siscont-1.onrender.com']

RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Configuración de la base de datos para producción
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Configuración de archivos estáticos para producción
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware de WhiteNoise ya está en base.py,
# pero asegúrate de que esté justo después de SecurityMiddleware:
# 'whitenoise.middleware.WhiteNoiseMiddleware' debe estar presente
