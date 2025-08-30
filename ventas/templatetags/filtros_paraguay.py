from django import template
from decimal import Decimal
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def pyg_intcomma(value):
    try:
        value = int(value)
        return f"{value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
    
@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_saldos(cuentas):
    return sum(cuenta.saldo for cuenta in cuentas)


@register.filter
def sum_attr(queryset, attr_name):
    """Suma los valores de un atributo específico en un queryset"""
    return sum(getattr(item, attr_name, Decimal('0')) for item in queryset)


@register.filter(name='sub')
def sub(value, arg):
    """Resta el arg del value"""
    try:
        if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
            return value - arg
        return value
    except (TypeError, ValueError):
        return value


@register.filter
def multiply(value, arg):
    """Multiplica dos valores"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide dos valores"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_field_label(form, field_name):
    """
    Obtiene el label de un campo de un formulario, con manejo seguro para campos no existentes.
    Devuelve el nombre del campo como fallback.
    """
    field = form.fields.get(field_name)
    if field and hasattr(field, 'label'):
        return escape(field.label)
    return escape(field_name.replace('_', ' ').title())




from decimal import Decimal, ROUND_HALF_UP

@register.filter
def pyg_decimal(value, decimal_places=2):
    """Formatea un decimal con el número específico de decimales"""
    if value is None:
        return "0.00"
    
    try:
        value = Decimal(value)
        # Redondear al número de decimales especificado
        rounded = value.quantize(Decimal('0.' + '0' * decimal_places), rounding=ROUND_HALF_UP)
        return format(rounded, f'.{decimal_places}f')
    except (TypeError, ValueError):
        return str(value)
    

@register.filter
def percentage(value, decimal_places=2):
    """Convierte un decimal a porcentaje"""
    try:
        return f"{float(value) * 100:.{decimal_places}f}%"
    except (TypeError, ValueError):
        return value

