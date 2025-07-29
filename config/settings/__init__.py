# config/settings/__init__.py
import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables del archivo .env

# Determina qué configuración cargar basado en DEBUG
if os.getenv('DEBUG', 'False').lower() in ('true', '1', 't'):
    from .development import *
else:
    from .production import *