# facturas/views.py
from datetime import date, datetime
from decimal import Decimal
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from .models import Cliente, Producto, Factura
from .forms import ClienteForm, ProductoForm, FacturaForm, FacturaDetalleForm
from sifen.core.builders.xml_builder import XMLBuilder
from sifen.core.signers.signer import firmar_xml

# Vistas para Cliente
class ClienteListView(ListView):
    model = Cliente
    template_name = 'facturas/cliente_list.html'

class ClienteCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'facturas/cliente_form.html'
    success_url = reverse_lazy('cliente-list')

class ClienteUpdateView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'facturas/cliente_form.html'
    success_url = reverse_lazy('cliente-list')

class ClienteDeleteView(DeleteView):
    model = Cliente
    template_name = 'facturas/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente-list')



# Vistas para Cliente
class ProductoListView(ListView):
    model = Producto
    template_name = 'facturas/producto_list.html'


# Vistas para Factura
class FacturaCreateView(CreateView):
    model = Factura
    form_class = FacturaForm
    template_name = 'facturas/factura_form.html'
    
    def form_valid(self, form):
        # Asignar número de factura automático (implementar lógica real)
        form.instance.numero = "001-001-0000001"  
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('factura-detail', kwargs={'pk': self.object.pk})

class FacturaDetailView(DetailView):
    model = Factura
    template_name = 'facturas/factura_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detalle_form'] = FacturaDetalleForm()
        return context

def agregar_detalle(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        form = FacturaDetalleForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.factura = factura
            detalle.precio_unitario = detalle.producto.precio
            detalle.save()
    return redirect('factura-detail', pk=pk)

def generar_xml_factura(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    
    # Convertir a modelo SIFEN (implementar esta conversión)
    from sifen.models.factura import Factura as SifenFactura
    from sifen.models.emisor import Emisor
    from sifen.models.receptor import Receptor
    from sifen.models.transportista import Transportista
    from sifen.models.vehiculo_transporte import VehiculoTransporte
    from sifen.models.punto_transporte import PuntoTransporte
    from sifen.models.datos_transporte import DatosTransporte
    from sifen.models.datos_supermercado import DatosSupermercado
    from sifen.models.datos_energia import DatosEnergia
    from sifen.models.item import ItemFactura
    from sifen.models.PolizaSeguro import PolizaSeguro
    from sifen.models.DatosSeguros import DatosSeguros
    from sifen.models.cuota import Cuota
    
    # Datos de ejemplo - reemplazar con tus datos reales
    emisor = Emisor(
            ruc="80012345",
            dv="1",
            nombre="TECNOLOGIA PY SA",
            nombre_fantasia="COMPUMUNDO",
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
        )


    transportista = Transportista(
            naturaleza="1",  # Persona jurídica
            nombre="TRANSPORTES DEL PARAGUAY S.A.",
            ruc="80054321",
            dv="3",
            chofer_identificacion="1234567",
            chofer_nombre="Carlos Giménez",
            domicilio_fiscal="Av. Mcal. López 2345",
            nacionalidad="PRY"
        )

    vehiculo = VehiculoTransporte(
            tipo_vehiculo="Camión",
            marca="Volvo",
            tipo_identificacion=1,
            numero_identificacion="CHS-123456",
            matricula="ABC123"
        )
        
        # Crear puntos de transporte
    punto_salida = PuntoTransporte(
            direccion="Av. República 123",
            numero_casa="456",
            departamento="1",  # Asunción
            ciudad="1"  # Asunción
        )

        # Crear puntos de transporte entrega
    punto_llegada = PuntoTransporte(
            direccion="Av. Pinedo",
            numero_casa="456",
            departamento="2",  # Asunción
            ciudad="3"  # Asunción
        )
        
        # Crear datos de transporte
    datos_transporte = DatosTransporte(
            tipo_transporte= "1", #1 propio, 2 tercero
            modalidad_transporte="1",  # Terrestre
            responsable_flete="1",  # Emisor
            condiciones_negocio= "CFR", #"CFR":"Costo y flete"
            numero_manifiesto="MAN-2023-001",
            numero_despacho_importacion= "nodesp1111111111", #16 caracteres fijos
            fecha_inicio_transporte= "2023-05-31",
            fecha_fin_transporte= "2023-07-12",
            pais_destino= "DZA",
            punto_salida=punto_salida,
            punto_llegada= punto_llegada,
            vehiculos=[vehiculo],
            transportista= transportista,
        )


    datos_supermercado = DatosSupermercado(
            nombre_cajero="Juan Pérez",
            efectivo=1500000,
            vuelto=2500,
            donacion=10000,
            descripcion_donacion="Donación voluntaria"
        )
        
    receptor = Receptor(
            ruc="1234567",
            dv="2",
            nombre="CLIENTE EJEMPLO",
            direccion="Calle Django 456",
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

        )

    datos_energia = DatosEnergia(
            numero_medidor="MED123456789",
            codigo_actividad=1,  # Código según tabla de actividades
            codigo_categoria="RES",  # RES=Residencial, COM=Comercial, etc.
            lectura_anterior=1250,
            lectura_actual=1350,
            consumo_kwh=100
        )

    items = [
            ItemFactura(
                codigo="PROD-001",
                descripcion="Laptop Premium",
                cantidad=2,
                precio_unitario=7500000,
                tasa_iva=10,
                codigo_producto="1234567890123",  # GTIN/EAN
                codigo_unidad_medida_comercial="UNI",
                numero_serie="SN-2023-01",
                liq_IVA= round(15000000/11,0)
            ),
            ItemFactura(
                codigo="PROD-002",
                descripcion="Teclado inalámbrico",
                cantidad=5,
                precio_unitario=150000,
                tasa_iva=10,
                codigo_producto="9876543210987",
                codigo_unidad_medida_comercial="UNI",
                liq_IVA= round(15000000/11,0)
            ),
            ItemFactura(
                codigo="IMP-003",
                descripcion="Impresora multifunción",
                cantidad=1,
                precio_unitario=1200000,
                tasa_iva=10,
                codigo_producto="5678901234567",
                codigo_unidad_medida_comercial="UNI",
                numero_lote="LOTE-IMP-2023",
                fecha_vencimiento=date(2025, 12, 31),
                liq_IVA= round(15000000/11,0)
          
            ),
            ItemFactura(
                codigo="IMP-004",
                descripcion="Producto importado",
                cantidad=3,
                precio_unitario=500000,
                tasa_iva=10,
                codigo_partida_arancelaria="8471", #debe ser entero de 4 digitos exactos
                codigo_nandina="84716090", #debe tener de 6 a 8 digitos enteros positivos
                pais_origen="BRA",
                nombre_pais_origen="BRASIL",
                codigo_unidad_medida_comercial="UNI",
                liq_IVA= round(15000000/11,0)
            )
        ]
        
    poliza1 = PolizaSeguro(
            numero_poliza="POL-2023-001",
            unidad_vigencia="MESES",
            vigencia="12",
            numero_poliza_completo="POLIZA-COMPLETA-2023-001",
            fecha_inicio_vigencia=datetime(day=1,month=1,year=2022).strftime("%Y-%m-%d"),
            fecha_fin_vigencia=datetime(day=1,month=1,year=2023).strftime("%Y-%m-%d"),
            codigo_interno="SEG-INT-001"
        )
        
    datos_seguros = DatosSeguros(
            codigo_empresa="ASEG123",
            polizas=[poliza1]
        )
    
    factura_sifen = SifenFactura(
        datos_energia=datos_energia,
        datos_seguros= datos_seguros,
        datos_supermercado= datos_supermercado,
        datos_transporte=datos_transporte,
        emisor=emisor,
        receptor=receptor,
        items=items,
        timbrado="12345678",
        serie_timbrado="CD",
        inicio_vig_timbrado= datetime(day=1,month=1,year=2025).strftime("%Y-%m-%d"),
        numero_factura="001-002-0000005",
        tipo_operacion="2",
        tipo_emision="1",
        condicion_venta="2",#Credito
        tipo_credito="1",#Cuotas
        tipo_impuesto_afectado="5",
        moneda= "PYG",
        plazo_credito="30 días",
        cuotas=[
            Cuota(numero=1, monto=Decimal("500000"), moneda= "PYG", fecha_vencimiento=date(2025, 6, 1)),
            Cuota(numero=2, monto=Decimal("500000"), moneda= "PYG", fecha_vencimiento=date(2025, 7, 1))
        ],


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
    
    # Generar y firmar XML
    xml = XMLBuilder().build(factura_sifen)
    xml_firmado = firmar_xml(xml)
    
    # Guardar XML en la factura
    factura.xml_generado = xml_firmado.decode('utf-8')
    factura.estado = 'G'
    factura.save()
    
    return redirect('factura-detail', pk=pk)