# services/sifen.py
import requests
from django.conf import settings
from django.utils import timezone
from ..models import DocumentoElectronico
from sifen.core.builders.xml_builder import XMLBuilder
from sifen.core.signers.signer import firmar_xml
from datetime import datetime
from decimal import Decimal

class SifenService:
    @classmethod
    def generar_documento(cls, venta, firmar=True):
        try:
            # Verificar si ya existe un documento
            doc, created = DocumentoElectronico.objects.get_or_create(
                venta=venta,
                defaults={'estado': 'NO_GENERADO'}
            )

            # Generar XML
            factura_sifen = cls._adaptar_venta(venta)
            xml = XMLBuilder().build(factura_sifen)
            
            doc.xml_generado = xml
            doc.estado = 'BORRADOR'
            
            if firmar:
                doc.xml_firmado = firmar_xml(xml).decode('utf-8')
                doc.estado = 'VALIDADO'
            
            doc.save()
            return doc

        except Exception as e:
            if hasattr(doc, 'pk'):
                doc.marcar_como_error(e)
            raise

    @classmethod
    def enviar_al_set(cls, documento):
        try:
            if not documento.xml_firmado:
                raise ValueError("No hay XML firmado para enviar")

            headers = {
                'Authorization': f'Bearer {settings.SIFEN_API_KEY}',
                'Content-Type': 'application/xml'
            }

            response = requests.post(
                settings.SIFEN_API_ENDPOINT,
                data=documento.xml_firmado,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if data.get('estado') == 'ok':
                documento.marcar_como_aceptado(data)
                documento.codigo_set = data['numero']
                documento.qr_url = data['qr_url']
                return True
            else:
                raise ValueError(data.get('error', 'Error desconocido del SET'))

        except Exception as e:
            documento.marcar_como_error(e)
            return False


    @staticmethod
    def _adaptar_venta(venta):
        """
        Adapta el modelo Venta a la estructura esperada por SIFEN
        """
        from sifen.models.factura import Factura as SifenFactura
        from sifen.models.emisor import Emisor
        from sifen.models.receptor import Receptor
        from sifen.models.item import ItemFactura
        from decimal import Decimal

        # Emisor (debería venir de settings o de un modelo Configuracion)
        emisor = Emisor(
            ruc='5886702',
            dv='3',
            nombre='PARRA SOLUCIONES EMPRESARIALES EAS',
            nombre_fantasia= 'PARRA COMPANY',
            direccion="Tte. Fariña e/Rojas Silva ",
            num_casa="456",
            c_departamento="2",
            c_distrito="7",
            c_ciudad="1046",
            telefono="0975-257-307",
            email="ventas@tecnologia.py",
            c_actividad_economica="69201",
            c_tipo_regimen="1",
            c_tipo_contibuyente="2",
            sucursal= "CASA MATRIZ",
            direccion_comp1="yamil armele y curupayty",
            direccion_comp2="pte franco y tte fariña",
            tipo_doc_responsable_DE="2",
            num_doc_responsable_DE="5886702",
            nombre_responsable_DE="Wilson Javier parra villa",
            cargo_responsable_DE="Cajero",
            is_sector_energia= False,
            is_sector_seguros= False,
            is_sector_supermercado= False,
            is_sector_transporte= False
            # ... completar con todos los campos requeridos
        )
        
        # Receptor (cliente)
        cliente = venta.cliente
        receptor = Receptor(
            ruc=cliente.numero_documento,
            dv=cliente.dv or '0',
            nombre=cliente.nombre_completo,
            direccion=cliente.direccion,

            pais="PRY",
            c_departamento="1",
            c_distrito="1",
            c_ciudad="1",
            telefono="(032)222210",
            celular="(0975)257-307",
            tipo_contribuyente="1",
            codigo_cliente="COD0102",
            nat_receptor="1", #1 es contribuyente
            tipo_doc_sin_ruc="5",
            nombre_fantasia="Nombe de fantasia recep",
            email="wilsonccont@gmail.com"
            # ... otros campos requeridos
        )
        
        # Items
        items = []
        for detalle in venta.detalles.all():
            if detalle.tasa_iva == 10:
                ival= round(detalle.precio_unitario /11,0)
            elif detalle.tasa_iva == 5:
                ival=  round(detalle.precio_unitario /21,0)

            items.append(ItemFactura(
                codigo=detalle.producto.codigo,
                descripcion=detalle.producto.nombre,
                cantidad=detalle.cantidad,
                precio_unitario=Decimal(str(detalle.precio_unitario)),
                tasa_iva=detalle.tasa_iva,

                codigo_producto="1234567890123",  # GTIN/EAN
                codigo_unidad_medida_comercial="UNI",
                numero_serie="SN-2023-01",
                liq_IVA= ival

            ))
        
        return SifenFactura(
            datos_energia= None,
            datos_seguros= None,
            datos_supermercado= None,
            datos_transporte= None,
            emisor=emisor,
            receptor=receptor,
            items=items,
            tipo_operacion="1",  # Venta de mercadería
            condicion_venta=venta.condicion,  # '1'=Contado, '2'=Crédito
            moneda="PYG",
            # ... completar con timbrado, series, etc.
            timbrado="12345678",
            serie_timbrado="CD",
            inicio_vig_timbrado= datetime(day=1,month=1,year=2025).strftime("%Y-%m-%d"),
            numero_factura="001-002-0000005",
            tipo_emision="1",
            tipo_credito="1",#Cuotas
            tipo_impuesto_afectado="5",
            plazo_credito="30 días",
            orden_compra= "OC 001",
            orden_venta= "OV 001",
            num_asiento = "123",
            unidad_medida_total_vol = "110",#METROS CUBICOS
            total_vol_merc ="2000",
            unidad_medida_total_peso = "99",#TONELADAS
            total_peso_merc ="1500",
            id_carga ="1",# Mercaderias en cadena de frío
            condicion_tipo_cambio= "1", # 1 Global
            tipo_cambio_base= "7850.36",
            condicion_anticipo= "1" #1 anticipo global
        )