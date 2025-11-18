from rest_framework import serializers
from .models import (
    MadrePaciente, Embarazo, Parto, PartoComplicacion, 
    PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo
)


class MadrePacienteSerializer(serializers.ModelSerializer):
    """Serializador para modelo MadrePaciente con campos relacionados."""
    nacionalidad_nombre = serializers.CharField(source='fk_nacionalidad.nombre', read_only=True)
    pueblo_originario_nombre = serializers.CharField(source='fk_pueblo_originario.nombre', read_only=True)
    edad = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = MadrePaciente
        fields = [
            'id_madre', 'run', 'nombre', 'apellido_paterno', 'apellido_materno',
            'nombre_completo', 'edad', 'fecha_nacimiento', 'fk_nacionalidad',
            'nacionalidad_nombre', 'fk_pueblo_originario', 'pueblo_originario_nombre',
            'fecha_registro', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_registro', 'fecha_actualizacion']
    
    def get_edad(self, obj):
        """Calcula edad actual."""
        from datetime import date
        today = date.today()
        return today.year - obj.fecha_nacimiento.year - (
            (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
        )
    
    def get_nombre_completo(self, obj):
        """Retorna nombre completo."""
        return obj.nombre_completo()


class EmbarazoSerializer(serializers.ModelSerializer):
    """Serializador para modelo Embarazo con datos de madre."""
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    trimestre = serializers.SerializerMethodField()
    viable = serializers.SerializerMethodField()
    
    class Meta:
        model = Embarazo
        fields = [
            'id_embarazo', 'fk_madre', 'madre_nombre', 'madre_run',
            'fecha_ultima_menstruacion', 'semana_obstetrica', 'trimestre',
            'viable', 'fecha_registro', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_registro', 'fecha_actualizacion']
    
    def get_trimestre(self, obj):
        """Retorna trimestre actual."""
        return obj.obtener_trimestre()
    
    def get_viable(self, obj):
        """Retorna si el embarazo es viable."""
        return obj.es_embarazo_viables()


class PartoComplicacionSerializer(serializers.ModelSerializer):
    """Serializador para complicaciones de parto."""
    complicacion_nombre = serializers.CharField(source='fk_complicacion.nombre', read_only=True)
    
    class Meta:
        model = PartoComplicacion
        fields = [
            'id_complicacion', 'fk_parto', 'fk_complicacion',
            'complicacion_nombre', 'fecha_registro'
        ]
        read_only_fields = ['fecha_registro']


class PartoAnestesiaSerializer(serializers.ModelSerializer):
    """Serializador para anestesia de parto."""
    tipo_anestesia_display = serializers.CharField(source='get_tipo_anestesia_display', read_only=True)
    
    class Meta:
        model = PartoAnestesia
        fields = [
            'id_anestesia', 'fk_parto', 'tipo_anestesia', 'tipo_anestesia_display',
            'solicitada_por_paciente', 'fecha_registro'
        ]
        read_only_fields = ['fecha_registro']


class PartoDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para Parto con complicaciones y anestesias anidadas."""
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    tipo_parto_nombre = serializers.CharField(source='fk_tipo_parto.nombre', read_only=True)
    profesional_nombre = serializers.CharField(source='fk_profesional_responsable.nombre_completo', read_only=True)
    clasificacion_robson_grupo = serializers.CharField(source='fk_clasificacion_robson.grupo', read_only=True)
    complicaciones = PartoComplicacionSerializer( many=True, read_only=True)
    anestesias = PartoAnestesiaSerializer(many=True, read_only=True)
    tuvo_complicaciones = serializers.SerializerMethodField()
    
    class Meta:
        model = Parto
        fields = [
            'id_parto', 'fk_madre', 'madre_nombre', 'madre_run',
            'fk_tipo_parto', 'tipo_parto_nombre', 'fk_profesional_responsable',
            'profesional_nombre', 'fk_clasificacion_robson', 'clasificacion_robson_grupo',
            'horas_trabajo_parto', 'complicaciones', 'anestesias', 'tuvo_complicaciones',
            'fecha_parto', 'fecha_registro', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_registro', 'fecha_actualizacion']
    
    def get_tuvo_complicaciones(self, obj):
        """Indica si el parto tuvo complicaciones."""
        return obj.tuvo_complicaciones()


class PartoSerializer(serializers.ModelSerializer):
    """Serializador para Parto (sin nidación de complicaciones)."""
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    tipo_parto_nombre = serializers.CharField(source='fk_tipo_parto.nombre', read_only=True)
    profesional_nombre = serializers.CharField(source='fk_profesional_responsable.nombre_completo', read_only=True)
    
    class Meta:
        model = Parto
        fields = [
            'id_parto', 'fk_madre', 'madre_nombre', 'madre_run',
            'fk_tipo_parto', 'tipo_parto_nombre', 'fk_profesional_responsable',
            'profesional_nombre', 'horas_trabajo_parto',
            'fecha_parto', 'fecha_registro', 'fecha_actualizacion'
        ]
        read_only_fields = ['fecha_registro', 'fecha_actualizacion']


class IVEAcompanamientoSerializer(serializers.ModelSerializer):
    """Serializador para acompañamiento de IVE."""
    tipo_profesional_display = serializers.CharField(source='get_tipo_profesional_display', read_only=True)
    
    class Meta:
        model = IVEAcompanamiento
        fields = [
            'id_acomp_ive', 'fk_ive_atencion', 'tipo_profesional',
            'tipo_profesional_display', 'fecha_atencion'
        ]
        read_only_fields = ['fecha_atencion']


class IVEAtencionDetailSerializer(serializers.ModelSerializer):
    """Serializador detallado para IVE con acompañamientos anidados."""
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    acompañamientos = IVEAcompanamientoSerializer(many=True, read_only=True)
    
    class Meta:
        model = IVEAtencion
        fields = [
            'id_ive_atencion', 'fk_madre', 'madre_nombre', 'madre_run',
            'fk_causal', 'edad_gestacional_semanas',
            'acompañamientos', 'fecha_atencion'
        ]
        read_only_fields = ['fecha_atencion']


class IVEAtencionSerializer(serializers.ModelSerializer):
    """Serializador para IVE (sin nidación de acompañamientos)."""
    madre_nombre = serializers.CharField(source='fk_madre.nombre', read_only=True)
    madre_run = serializers.CharField(source='fk_madre.run', read_only=True)
    
    class Meta:
        model = IVEAtencion
        fields = [
            'id_ive_atencion', 'fk_madre', 'madre_nombre', 'madre_run',
            'fk_causal', 'edad_gestacional_semanas', 'fecha_atencion'
        ]
        read_only_fields = ['fecha_atencion']


class AltaAnticonceptivoSerializer(serializers.ModelSerializer):
    """Serializador para Alta con Anticonceptivo."""
    tipo_alta_display = serializers.CharField(source='get_tipo_alta_display', read_only=True)
    metodo_display = serializers.CharField(source='get_fk_metodo_anticonceptivo_display', read_only=True)
    
    class Meta:
        model = AltaAnticonceptivo
        fields = [
            'id_alta_ac', 'fk_evento', 'tipo_alta', 'tipo_alta_display',
            'fk_metodo_anticonceptivo', 'metodo_display',
            'esterilizacion_quirurgica', 'fecha_registro'
        ]
        read_only_fields = ['fecha_registro']


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