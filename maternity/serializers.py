from rest_framework import serializers
from .models import MadrePaciente, Embarazo, Parto, PartoComplicacion, PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo


class MadrePacienteSerializer(serializers.ModelSerializer):
    nacionalidad_nombre = serializers.CharField(source='fk_nacionalidad.nombre', read_only=True)
    pueblo_originario_nombre = serializers.CharField(source='fk_pueblo_originario.nombre', read_only=True)
    
    class Meta:
        model = MadrePaciente
        fields = '__all__'


class EmbarazoSerializer(serializers.ModelSerializer):
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    
    class Meta:
        model = Embarazo
        fields = '__all__'


class PartoSerializer(serializers.ModelSerializer):
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    tipo_parto_nombre = serializers.CharField(source='fk_tipo_parto.nombre', read_only=True)
    profesional_nombre = serializers.CharField(source='fk_profesional_responsable.nombre_completo', read_only=True)
    clasificacion_robson_grupo = serializers.CharField(source='fk_clasificacion_robson.grupo', read_only=True)
    
    class Meta:
        model = Parto
        fields = '__all__'


class PartoComplicacionSerializer(serializers.ModelSerializer):
    parto_id = serializers.IntegerField(source='fk_parto.id_parto', read_only=True)
    complicacion_nombre = serializers.CharField(source='fk_complicacion.nombre', read_only=True)
    
    class Meta:
        model = PartoComplicacion
        fields = '__all__'


class PartoAnestesiaSerializer(serializers.ModelSerializer):
    parto_id = serializers.IntegerField(source='fk_parto.id_parto', read_only=True)
    
    class Meta:
        model = PartoAnestesia
        fields = '__all__'


class IVEAtencionSerializer(serializers.ModelSerializer):
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    
    class Meta:
        model = IVEAtencion
        fields = '__all__'


class IVEAcompanamientoSerializer(serializers.ModelSerializer):
    ive_id = serializers.IntegerField(source='fk_ive_atencion.id_ive_atencion', read_only=True)
    
    class Meta:
        model = IVEAcompanamiento
        fields = '__all__'


class AltaAnticonceptivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AltaAnticonceptivo
        fields = '__all__'