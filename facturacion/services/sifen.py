# services/sifen.py
import requests
import pdfkit  # Necesitarás instalar esta librería: pip install pdfkit
import logging
from django.conf import settings
from config.settings import base
from django.utils import timezone
from ..models import DocumentoElectronico
from sifen.core.builders.xml_builder import XMLBuilder
from sifen.core.signers.signer import firmar_xml
from datetime import datetime
from decimal import Decimal
from empresa.models import Empresa, ActividadesEconomicas, Sucursal


#from config.settings import development as settings
from .mock_services import MockSifenService

# Configuración del logger
logger = logging.getLogger(__name__)

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
            documento.marcar_como_enviado()
            
            if settings.USE_SIFEN_MOCK:
                from .mock_services import MockSifenService
                response = MockSifenService.enviar_documento(documento.xml_firmado)
            else:
                headers = {
                    'Authorization': f'Bearer {settings.SIFEN_CONFIG["API_KEY"]}',
                    'Content-Type': 'application/xml'
                }
                response = requests.post(
                    settings.SIFEN_CONFIG["ENDPOINT"],
                    data=documento.xml_firmado,
                    headers=headers,
                    timeout=settings.SIFEN_CONFIG["TIMEOUT"]
                ).json()
            
            if response.get('estado') == 'VALIDO':
                documento.marcar_como_aceptado(response)
                return True
            else:
                documento.marcar_como_rechazado(response)
                return False
                
        except Exception as e:
            documento.estado = 'ERROR'
            documento.errores = str(e)
            documento.save()
            logger.error(f"Error enviando documento {documento.pk} al SET: {str(e)}")
            return False




    @staticmethod
    def _adaptar_venta(venta):
        """
        Adapta el modelo Venta a la estructura esperada por SIFEN
        """
        from sifen.models.factura import Factura as SifenFactura
        from sifen.models.emisor import Emisor
        from sifen.models.item_actividades import ItemActividades
        from sifen.models.receptor import Receptor
        from sifen.models.item import ItemFactura
        from decimal import Decimal
        
        # Obtener la empresa (asumiendo que hay una relación o que es única)
        empresa = Empresa.objects.first()  # O usar venta.empresa si hay relación

        # Obtener las acitividades económicas de la empresa
        actividades = ActividadesEconomicas.objects.filter(empresa=empresa).order_by('id')

        # Obtener la sucursal
        sucursal = Sucursal.objects.get(pk = venta.caja.punto_expedicion.sucursal.id)

        # Items actividades economicas
        items_act = []
        for act in actividades:
            
            items_act.append(ItemActividades(
                codigo=act.codigo,
                descripcion= act.descripcion,
            ))

        # Emisor (debería venir de settings o de un modelo Configuracion)
        emisor = Emisor(
            ruc= empresa.ruc,
            dv= empresa.dv,
            nombre= empresa.nombre,
            nombre_fantasia= empresa.nombre_comercial,
            direccion= empresa.direccion,
            num_casa= empresa.num_casa,
            c_departamento= empresa.departamento_codigo,
            c_distrito= empresa.distrito_codigo,
            c_ciudad= empresa.ciudad_codigo,
            telefono= empresa.telefono,
            email= empresa.email,
            c_actividad_economica= items_act,
            c_tipo_contibuyente= empresa.t_contribuyente,
            c_tipo_regimen= empresa.regimen, 
            sucursal= sucursal.nombre,
            direccion_comp1= empresa.calle_sec,
            direccion_comp2= empresa.no_edificio,
            tipo_doc_responsable_DE= venta.caja.responsable.tipo_doc,
            num_doc_responsable_DE= venta.caja.responsable.cedula,
            nombre_responsable_DE= venta.caja.responsable.usuario.first_name + venta.caja.responsable.usuario.last_name,
            cargo_responsable_DE= venta.caja.responsable.tipo_usuario,
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
            pais= cliente.pais_cod,
            c_departamento="1",
            c_distrito="1",
            c_ciudad="1",
            telefono= cliente.telefono,
            celular= cliente.telefono,
            tipo_contribuyente= cliente.t_contribuyente,
            codigo_cliente= "001",
            nat_receptor= cliente.naturaleza, #1 es contribuyente
            tipo_doc_sin_ruc= cliente.tipo_documento,
            nombre_fantasia="Nombe de fantasia recep",
            email= cliente.email
            # ... otros campos requeridos
        )
        
        # Items
        items = []
        for detalle in venta.detalles.all():
            if detalle.tasa_iva == 10:
                ival= round(detalle.precio_unitario /11,0)
            elif detalle.tasa_iva == 5:
                ival=  round(detalle.precio_unitario /21,0)
            
            print(detalle.producto.unidad_medida.abreviatura_sifen)

            items.append(ItemFactura(
                codigo=detalle.producto.codigo,
                descripcion=detalle.producto.nombre,
                cantidad=detalle.cantidad,
                precio_unitario=Decimal(str(detalle.precio_unitario)),
                tasa_iva=detalle.tasa_iva,

                codigo_producto="1234567890123",  # GTIN/EAN
                unidad_medida= detalle.producto.unidad_medida.abreviatura_sifen,
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
            timbrado= venta.timbrado.numero,
            serie_timbrado="CD",
            inicio_vig_timbrado= venta.timbrado.fecha_inicio.strftime("%Y-%m-%d"),
            numero_factura= venta.numero_documento,
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
    




    @classmethod
    def generar_kude(cls, documento):
        """
        Genera el KUDE (PDF) a partir del XML firmado
        """
        try:
            # Configuración de pdfkit (ajusta la ruta según tu sistema)

            #config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)
            config = pdfkit.configuration(wkhtmltopdf= base.WKHTMLTOPDF_PATH)
            
            # Contexto para la plantilla
            context = {
                'documento': documento,
                'venta': documento.venta,
                'detalles': documento.venta.detalles.all(),
                'fecha': timezone.now().strftime("%d/%m/%Y %H:%M")
            }
            
            # Renderizar plantilla HTML
            from django.template.loader import render_to_string
            html_content = render_to_string('facturacion/kude_template.html', context)
            
            # Convertir HTML a PDF
            pdf = pdfkit.from_string(html_content, False, configuration=config)
            
            # Guardar el PDF
            documento.kude_pdf = pdf
            documento.kude_generado = True
            documento.fecha_generacion_kude = timezone.now()
            documento.save()
            
            return True
        except Exception as e:
            documento.errores = f"Error al generar KUDE: {str(e)}"
            documento.save()
            logger.error(f"Error generando KUDE: {str(e)}", exc_info=True)
            return False

    
       