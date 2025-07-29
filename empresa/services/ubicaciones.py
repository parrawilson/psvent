# empresa/services/ubicaciones.py
import json
from django.conf import settings
import os

class UbicacionesService:
    _instance = None
    _data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UbicacionesService, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        """Carga los datos del archivo JSON una sola vez"""
        if self._data is None:
            file_path = os.path.join(settings.BASE_DIR, 'departamentos_distritos_ciudades.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)

    def get_departamentos(self):
        """Obtiene todos los departamentos"""
        return [{'codigo': str(depto['codigo']), 'nombre': depto['nombre']} 
                for depto in self._data]

    def get_distritos(self, departamento_codigo):
        """Obtiene distritos por código de departamento"""
        for depto in self._data:
            if str(depto['codigo']) == str(departamento_codigo):
                return [{'codigo': str(dist['codigo']), 'nombre': dist['nombre']}
                       for dist in depto.get('distritos', [])]
        return []

    def get_ciudades(self, departamento_codigo, distrito_codigo):
        """Obtiene ciudades por código de departamento y distrito"""
        for depto in self._data:
            if str(depto['codigo']) == str(departamento_codigo):
                for dist in depto.get('distritos', []):
                    if str(dist['codigo']) == str(distrito_codigo):
                        return [{'codigo': str(ciudad['codigo']), 'nombre': ciudad['nombre']}
                               for ciudad in dist.get('ciudades', [])]
        return []

    def get_barrios(self, departamento_codigo, distrito_codigo, ciudad_codigo):
        """Obtiene barrios por códigos de departamento, distrito y ciudad"""
        for depto in self._data:
            if str(depto['codigo']) == str(departamento_codigo):
                for dist in depto.get('distritos', []):
                    if str(dist['codigo']) == str(distrito_codigo):
                        for ciudad in dist.get('ciudades', []):
                            if str(ciudad['codigo']) == str(ciudad_codigo):
                                return [{'codigo': str(barrio['codigo']), 'nombre': barrio['nombre']}
                                       for barrio in ciudad.get('barrios', [])]
        return []

    def get_nombre_departamento(self, codigo):
        """Obtiene el nombre de un departamento por su código"""
        for depto in self._data:
            if str(depto['codigo']) == str(codigo):
                return depto['nombre']
        return ""

    def get_nombre_distrito(self, depto_codigo, distrito_codigo):
        """Obtiene el nombre de un distrito por su código"""
        for depto in self._data:
            if str(depto['codigo']) == str(depto_codigo):
                for dist in depto.get('distritos', []):
                    if str(dist['codigo']) == str(distrito_codigo):
                        return dist['nombre']
        return ""

    def get_nombre_ciudad(self, depto_codigo, distrito_codigo, ciudad_codigo):
        """Obtiene el nombre de una ciudad por su código"""
        for depto in self._data:
            if str(depto['codigo']) == str(depto_codigo):
                for dist in depto.get('distritos', []):
                    if str(dist['codigo']) == str(distrito_codigo):
                        for ciudad in dist.get('ciudades', []):
                            if str(ciudad['codigo']) == str(ciudad_codigo):
                                return ciudad['nombre']
        return ""

    def get_nombre_barrio(self, depto_codigo, distrito_codigo, ciudad_codigo, barrio_codigo):
        """Obtiene el nombre de un barrio por su código"""
        for depto in self._data:
            if str(depto['codigo']) == str(depto_codigo):
                for dist in depto.get('distritos', []):
                    if str(dist['codigo']) == str(distrito_codigo):
                        for ciudad in dist.get('ciudades', []):
                            if str(ciudad['codigo']) == str(ciudad_codigo):
                                for barrio in ciudad.get('barrios', []):
                                    if str(barrio['codigo']) == str(barrio_codigo):
                                        return barrio['nombre']
        return ""