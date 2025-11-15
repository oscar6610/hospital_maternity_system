from django.db import models
from catalogs.models import CatNacionalidad, CatPuebloOriginario, CatComplicacionParto, CatRobson, CatTipoParto
from core.models import Usuario


class MadrePaciente(models.Model):
    id_madre = models.AutoField(primary_key=True)
    run = models.CharField(max_length=15, unique=True)
    nombre = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    edad = models.IntegerField()
    fk_nacionalidad = models.ForeignKey(CatNacionalidad, on_delete=models.PROTECT, db_column='fk_nacionalidad')
    fk_pueblo_originario = models.ForeignKey(CatPuebloOriginario, on_delete=models.SET_NULL, null=True, blank=True, db_column='fk_pueblo_originario')
    discapacidad_senadis = models.BooleanField(default=False)
    privada_de_libertad = models.BooleanField(default=False)
    trans_masculino_no_binarie = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'madre_paciente'
        verbose_name = 'Madre Paciente'
        verbose_name_plural = 'Madres Pacientes'
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.run})"


class Embarazo(models.Model):
    id_embarazo = models.AutoField(primary_key=True)
    fk_madre = models.ForeignKey(MadrePaciente, on_delete=models.CASCADE, db_column='fk_madre')
    paridad = models.IntegerField()
    control_prenatal = models.BooleanField(default=True)
    semana_obstetrica = models.IntegerField()
    riesgo_obstetrico = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = 'embarazo'
        verbose_name = 'Embarazo'
        verbose_name_plural = 'Embarazos'
    
    def __str__(self):
        return f"Embarazo {self.id_embarazo} - {self.fk_madre.nombre}"


class Parto(models.Model):
    id_parto = models.AutoField(primary_key=True)
    fk_madre = models.ForeignKey(MadrePaciente, on_delete=models.CASCADE, db_column='fk_madre')
    fk_tipo_parto = models.ForeignKey(CatTipoParto, on_delete=models.PROTECT, db_column='fk_tipo_parto')
    fecha_hora_parto = models.DateTimeField()
    es_parto_multiple = models.BooleanField(default=False)
    fk_clasificacion_robson = models.ForeignKey(CatRobson, on_delete=models.PROTECT, null=True, blank=True, db_column='fk_clasificacion_robson')
    fk_profesional_responsable = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='fk_profesional_responsable')
    plan_de_parto = models.BooleanField(default=False)
    fk_origen_ingreso = models.CharField(max_length=50, blank=True, null=True)
    libertad_movimiento = models.BooleanField(default=False)
    fk_posicion_parto = models.CharField(max_length=50, blank=True, null=True)
    fk_estado_perine = models.CharField(max_length=50, blank=True, null=True)
    fk_acompanante = models.CharField(max_length=100, blank=True, null=True)
    fk_sala_duelo_perinatal = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'parto'
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'
    
    def __str__(self):
        return f"Parto {self.id_parto} - {self.fk_madre.nombre} - {self.fecha_hora_parto}"


class PartoComplicacion(models.Model):
    id_parto_complicacion = models.AutoField(primary_key=True)
    fk_parto = models.ForeignKey(Parto, on_delete=models.CASCADE, db_column='fk_parto')
    fk_complicacion = models.ForeignKey(CatComplicacionParto, on_delete=models.PROTECT, db_column='fk_complicacion')
    fk_causa_hpp = models.CharField(max_length=50, blank=True, null=True)
    histerectomia_obstetrica = models.BooleanField(default=False)
    transfusion_sanguinea = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'parto_complicacion'
        verbose_name = 'Complicación de Parto'
        verbose_name_plural = 'Complicaciones de Parto'
    
    def __str__(self):
        return f"Complicación Parto {self.fk_parto.id_parto} - {self.fk_complicacion.nombre}"


class PartoAnestesia(models.Model):
    id_anestesia = models.AutoField(primary_key=True)
    fk_parto = models.ForeignKey(Parto, on_delete=models.CASCADE, db_column='fk_parto')
    tipo_anestesia = models.CharField(max_length=50)
    solicitada_por_paciente = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'parto_anestesia'
        verbose_name = 'Anestesia de Parto'
        verbose_name_plural = 'Anestesias de Parto'
    
    def __str__(self):
        return f"Anestesia Parto {self.fk_parto.id_parto} - {self.tipo_anestesia}"


class IVEAtencion(models.Model):
    id_ive_atencion = models.AutoField(primary_key=True)
    fk_madre = models.ForeignKey(MadrePaciente, on_delete=models.CASCADE, db_column='fk_madre')
    fk_causal = models.CharField(max_length=10)
    edad_gestacional_semanas = models.IntegerField()
    fk_voluntad = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = 'ive_atencion'
        verbose_name = 'Atención IVE'
        verbose_name_plural = 'Atenciones IVE'
    
    def __str__(self):
        return f"IVE {self.id_ive_atencion} - {self.fk_madre.nombre}"


class IVEAcompanamiento(models.Model):
    id_acomp_ive = models.AutoField(primary_key=True)
    fk_ive_atencion = models.ForeignKey(IVEAtencion, on_delete=models.CASCADE, db_column='fk_ive_atencion')
    tipo_profesional = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'ive_acompanamiento'
        verbose_name = 'Acompañamiento IVE'
        verbose_name_plural = 'Acompañamientos IVE'
    
    def __str__(self):
        return f"Acompañamiento IVE {self.fk_ive_atencion.id_ive_atencion} - {self.tipo_profesional}"


class AltaAnticonceptivo(models.Model):
    id_alta_ac = models.AutoField(primary_key=True)
    fk_evento = models.IntegerField()
    tipo_alta = models.CharField(max_length=20)
    fk_metodo_anticonceptivo = models.IntegerField(null=True, blank=True)
    esterilizacion_quirurgica = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'alta_anticonceptivo'
        verbose_name = 'Alta con Anticonceptivo'
        verbose_name_plural = 'Altas con Anticonceptivo'
    
    def __str__(self):
        return f"Alta Anticonceptivo {self.id_alta_ac} - {self.tipo_alta}"