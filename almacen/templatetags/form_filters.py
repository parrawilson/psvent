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




