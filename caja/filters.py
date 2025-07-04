import django_filters
from .models import MovimientoCaja

class MovimientoFilter(django_filters.FilterSet):
    fecha_inicio = django_filters.DateFilter(
        field_name='fecha', 
        lookup_expr='gte',
        label='Desde'
    )
    fecha_fin = django_filters.DateFilter(
        field_name='fecha', 
        lookup_expr='lte',
        label='Hasta'
    )

    class Meta:
        model = MovimientoCaja
        fields = ['caja', 'tipo']