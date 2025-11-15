from rest_framework import serializers
from .models import ReporteREM, ReporteREMDetalle


class ReporteREMDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteREMDetalle
        fields = '__all__'


class ReporteREMSerializer(serializers.ModelSerializer):
    usuario_genera_nombre = serializers.CharField(source='fk_usuario_genera.nombre_completo', read_only=True)
    detalles = ReporteREMDetalleSerializer(many=True, read_only=True, source='reporteremdetalle_set')
    
    class Meta:
        model = ReporteREM
        fields = '__all__'
        read_only_fields = ['fecha_generacion']