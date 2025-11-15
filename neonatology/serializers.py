from rest_framework import serializers
from .models import RecienNacido, RNAtencionInmediata, RNTamizajeMetabolico, RNTamizajeAuditivo, RNTamizajeCardiopatia, RNEgreso


class RecienNacidoSerializer(serializers.ModelSerializer):
    parto_id = serializers.IntegerField(source='fk_parto.id_parto', read_only=True)
    madre_nombre = serializers.CharField(source='fk_parto.fk_madre.nombre', read_only=True)
    
    class Meta:
        model = RecienNacido
        fields = '__all__'


class RNAtencionInmediataSerializer(serializers.ModelSerializer):
    rn_id = serializers.IntegerField(source='fk_rn.id_rn', read_only=True)
    profesional_nombre = serializers.CharField(source='fk_profesional_registra.nombre_completo', read_only=True)
    
    class Meta:
        model = RNAtencionInmediata
        fields = '__all__'


class RNTamizajeMetabolicoSerializer(serializers.ModelSerializer):
    rn_id = serializers.IntegerField(source='fk_rn.id_rn', read_only=True)
    
    class Meta:
        model = RNTamizajeMetabolico
        fields = '__all__'


class RNTamizajeAuditivoSerializer(serializers.ModelSerializer):
    rn_id = serializers.IntegerField(source='fk_rn.id_rn', read_only=True)
    
    class Meta:
        model = RNTamizajeAuditivo
        fields = '__all__'


class RNTamizajeCardiopatiaSerializer(serializers.ModelSerializer):
    rn_id = serializers.IntegerField(source='fk_rn.id_rn', read_only=True)
    
    class Meta:
        model = RNTamizajeCardiopatia
        fields = '__all__'


class RNEgresoSerializer(serializers.ModelSerializer):
    rn_id = serializers.IntegerField(source='fk_rn.id_rn', read_only=True)
    
    class Meta:
        model = RNEgreso
        fields = '__all__'