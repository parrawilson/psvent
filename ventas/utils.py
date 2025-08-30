from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

def safe_decimal(value, decimals=2):
    """
    Convierte de forma segura un valor a Decimal con el número de decimales especificado
    """
    if value is None:
        return Decimal('0.00')
    
    try:
        if isinstance(value, Decimal):
            decimal_value = value
        else:
            decimal_value = Decimal(str(value))
        
        # Redondear al número de decimales especificado
        return decimal_value.quantize(Decimal(f'1.{ "0" * decimals }'), rounding=ROUND_HALF_UP)
        
    except (ValueError, InvalidOperation):
        return Decimal('0.00')