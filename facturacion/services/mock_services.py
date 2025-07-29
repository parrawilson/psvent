# facturacion/mock_services.py
import random
import time
from datetime import datetime

class MockSifenService:
    @classmethod
    def enviar_documento(cls, xml_firmado):
        # Simular tiempo de respuesta
        time.sleep(random.uniform(1, 3))
        
        # 20% de probabilidad de error
        if random.random() < 0.2:
            return {
                'estado': 'RECHAZADO',
                'mensaje': 'Error simulado: RUC del receptor no válido',
                'numero': None,
                'qr_url': None
            }
        
        # Simular respuesta exitosa
        numero = random.randint(1000000, 9999999)
        return {
            'estado': 'VALIDO',
            'mensaje': 'Documento electrónico validado correctamente',
            'numero': f"001-001-{numero:07d}",
            'qr_url': f"https://mock.sifen.gov.py/qr/{numero}"
        }