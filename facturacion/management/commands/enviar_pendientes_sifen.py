# management/commands/enviar_pendientes_sifen.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from facturacion.models import DocumentoElectronico
from facturacion.services import SifenService

class Command(BaseCommand):
    help = 'Envía documentos electrónicos pendientes al SET'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--max-intentos',
            type=int,
            default=3,
            help='Número máximo de intentos de envío'
        )
    
    def handle(self, *args, **options):
        max_intentos = options['max_intentos']
        pendientes = DocumentoElectronico.objects.filter(
            estado__in=['VALIDADO', 'ERROR'],
            intentos__lt=max_intentos
        ).select_related('venta')
        
        self.stdout.write(f"Encontré {pendientes.count()} documentos pendientes")
        
        for doc in pendientes:
            try:
                self.stdout.write(f"Procesando venta {doc.venta.numero}...")
                
                if SifenService.enviar_al_set(doc):
                    self.stdout.write(
                        self.style.SUCCESS(f"Documento {doc.codigo_set} aceptado")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Error en venta {doc.venta.numero}: {doc.errores}")
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error crítico: {str(e)}")
                )