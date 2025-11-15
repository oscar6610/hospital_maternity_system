from rest_framework import serializers
from .models import AlertaSistema


class AlertaSistemaSerializer(serializers.ModelSerializer):
    usuario_genera_nombre = serializers.CharField(source='fk_usuario_genera.nombre_completo', read_only=True)
    usuario_resuelve_nombre = serializers.CharField(source='fk_usuario_resuelve.nombre_completo', read_only=True)
    
    class Meta:
        model = AlertaSistema
        fields = '__all__'
        read_only_fields = ['fecha_hora']