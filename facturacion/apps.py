from django.apps import AppConfig

class FacturacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'facturacion'

    def ready(self):
        # Importa las señales solo cuando la app esté lista
        from . import signals