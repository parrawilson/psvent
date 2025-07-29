from django import template

register = template.Library()

@register.filter(name='add_attrs')
def add_attrs(field, args):
    """
    Uso: {{ field|add_attrs:"class=...,id=..." }}
    """
    attrs = {}
    for attr in args.split(','):
        key, val = attr.split('=')
        attrs[key.strip()] = val.strip()
    return field.as_widget(attrs={**field.field.widget.attrs, **attrs})


@register.filter(name='add_class')
def add_class(field, css):
    existing_classes = field.field.widget.attrs.get('class', '')
    new_classes = f'{existing_classes} {css}'.strip()
    return field.as_widget(attrs={**field.field.widget.attrs, 'class': new_classes})


@register.filter(name='format_ejemplo')
def format_ejemplo(formato, secuencia):
    """
    Genera un número de documento de ejemplo basado en el formato y la secuencia.
    Ejemplo: "001-001-0000001" donde:
    - 001 = código de sucursal
    - 001 = código de punto de expedición
    - 0000001 = número secuencial con padding de 7 dígitos
    """
    try:
        # Obtener valores necesarios con manejo de errores
        codigo_sucursal = getattr(secuencia.punto_expedicion.sucursal, 'codigo', '001')
        codigo_punto = getattr(secuencia.punto_expedicion, 'codigo', '001')
        prefijo = getattr(secuencia, 'prefijo', f"{codigo_sucursal}-{codigo_punto}")
        
        # Reemplazar variables en el formato
        ejemplo = (
            formato
            .replace('{prefijo}', prefijo)
            .replace('{sucursal}', codigo_sucursal)
            .replace('{punto}', codigo_punto)
            .replace('{numero:07d}', '0000001')  # Ejemplo con padding
            .replace('{numero}', '1')            # Ejemplo sin padding
        )
        
        # Si el formato está vacío o no contiene variables, usar formato por defecto
        if not any(var in formato for var in ['{prefijo}', '{sucursal}', '{punto}', '{numero}']):
            ejemplo = f"{codigo_sucursal}-{codigo_punto}-0000001"
            
        return ejemplo
        
    except (AttributeError, ObjectDoesNotExist) as e:
        # Fallback en caso de error
        return f"001-001-0000001 (Error: {str(e)})"


