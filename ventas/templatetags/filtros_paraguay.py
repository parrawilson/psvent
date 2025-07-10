from django import template

register = template.Library()

@register.filter
def pyg_intcomma(value):
    try:
        value = int(value)
        return f"{value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
