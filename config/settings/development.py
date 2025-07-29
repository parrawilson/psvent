# config/settings/development.py

from .base import *

DEBUG = True

#ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ALLOWED_HOSTS = ['*']  # solo para desarrollo


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


# Configuración específica para desarrollo
USE_SIFEN_MOCK = os.getenv('USE_SIFEN_MOCK', 'True') == 'True'

SIFEN_CONFIG.update({
    'ENDPOINT': 'http://localhost:8000/mock-sifen/',
    'API_KEY': os.getenv('SIFEN_API_KEY'),
    'CERTIFICADO': str(BASE_DIR / 'certs' / 'certificado_prueba.pfx'),
    'CERTIFICADO_PASSWORD': os.getenv('SIFEN_CERT_PASSWORD'),
    'WKHTMLTOPDF_PATH': os.getenv('WKHTMLTOPDF_PATH', '/usr/local/bin/wkhtmltopdf'),
})