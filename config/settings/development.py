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
