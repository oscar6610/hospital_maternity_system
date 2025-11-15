from rest_framework import serializers
from .models import TrazaMovimiento


class TrazaMovimientoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='fk_usuario.nombre_completo', read_only=True)
    
    class Meta:
        model = TrazaMovimiento
        fields = '__all__'
        read_only_fields = ['fecha_hora']