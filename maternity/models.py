from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from catalogs.models import CatNacionalidad, CatPuebloOriginario, CatComplicacionParto, CatRobson, CatTipoParto
from core.models import Usuario


class MadrePaciente(models.Model):
    """Modelo para gestionar información de madres pacientes en el sistema hospitalario."""
    
    id_madre = models.AutoField(primary_key=True)
    run = models.CharField(max_length=15, unique=True, help_text="RUT de la madre (ej: 12345678-9)")
    nombre = models.CharField(max_length=50, help_text="Nombre de la madre")
    apellido_paterno = models.CharField(max_length=50, help_text="Apellido paterno")
    apellido_materno = models.CharField(max_length=50, help_text="Apellido materno")
    fecha_nacimiento = models.DateField(help_text="Fecha de nacimiento de la madre")
    fk_nacionalidad = models.ForeignKey(CatNacionalidad, on_delete=models.PROTECT, db_column='fk_nacionalidad', help_text="Nacionalidad")
    fk_pueblo_originario = models.ForeignKey(
        CatPuebloOriginario, on_delete=models.SET_NULL, null=True, blank=True, 
        db_column='fk_pueblo_originario', help_text="Pueblo originario (opcional)"
    )
    discapacidad_senadis = models.BooleanField(default=False, help_text="Tiene discapacidad registrada en SENADIS")
    privada_de_libertad = models.BooleanField(default=False, help_text="Está privada de libertad")
    trans_masculino_no_binarie = models.BooleanField(default=False, help_text="Identidad de género diversa")
    fecha_registro = models.DateTimeField(auto_now_add=True, help_text="Fecha de registro en el sistema")
    fecha_actualizacion = models.DateTimeField(auto_now=True, help_text="Última actualización")
    
    class Meta:
        db_table = 'madre_paciente'
        verbose_name = 'Madre Paciente'
        verbose_name_plural = 'Madres Pacientes'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['run']),
            models.Index(fields=['nombre', 'apellido_paterno']),
        ]
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.run})"
    
    def nombre_completo(self):
        """Retorna el nombre completo de la madre."""
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
    
    def clean(self):
        """Validaciones a nivel de modelo."""
        from datetime import date
        today = date.today()
        edad = today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
        if edad < 0 or edad > 120:
            raise ValidationError({'fecha_nacimiento': 'La edad debe estar entre 0 y 120 años.'})
    
    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.clean()
        super().save(*args, **kwargs)


class Embarazo(models.Model):
    """Modelo para gestionar embarazos de madres pacientes."""
    
    id_embarazo = models.AutoField(primary_key=True)
    fk_madre = models.ForeignKey(MadrePaciente, on_delete=models.CASCADE, db_column='fk_madre', related_name='embarazos', help_text="Madre paciente")
    paridad = models.IntegerField(help_text="Número de embarazos previos")
    control_prenatal = models.BooleanField(default=True, help_text="¿Asistió a control prenatal?")
    fecha_ultima_menstruacion = models.DateField(help_text="Fecha de última menstruación")
    semana_obstetrica = models.IntegerField(
        help_text="Semana de gestación",
        validators=[MinValueValidator(0), MaxValueValidator(42)]
    )
    riesgo_obstetrico = models.CharField(max_length=50, blank=True, null=True, help_text="Clasificación de riesgo")
    fecha_registro = models.DateTimeField(auto_now_add=True, help_text="Fecha de registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, help_text="Última actualización")
    
    class Meta:
        db_table = 'embarazo'
        verbose_name = 'Embarazo'
        verbose_name_plural = 'Embarazos'
        ordering = ['-fecha_registro']
        unique_together = ('fk_madre', 'fecha_ultima_menstruacion')
    
    def __str__(self):
        return f"Embarazo {self.id_embarazo} - {self.fk_madre.nombre} ({self.semana_obstetrica}s)"
    
    def obtener_trimestre(self):
        """Retorna el trimestre actual del embarazo."""
        if self.semana_obstetrica is None:
            return None
        if self.semana_obstetrica <= 12:
            return 1
        elif self.semana_obstetrica <= 27:
            return 2
        else:
            return 3
    
    def es_embarazo_viables(self):
        """Verifica si es un embarazo viable (>= 20 semanas)."""
        if self.semana_obstetrica is None:
            return None
        return self.semana_obstetrica >= 20


class Parto(models.Model):
    """Modelo para gestionar datos de partos."""
    
    TIPO_PARTO_CHOICES = [
        ('vaginal', 'Parto Vaginal'),
        ('cesarea', 'Cesárea'),
        ('instrumental', 'Parto Instrumental'),
    ]
    
    id_parto = models.AutoField(primary_key=True)
    fk_madre = models.ForeignKey(MadrePaciente, on_delete=models.CASCADE, db_column='fk_madre', related_name='partos', help_text="Madre paciente")
    fk_tipo_parto = models.ForeignKey(CatTipoParto, on_delete=models.PROTECT, db_column='fk_tipo_parto', help_text="Tipo de parto")
    fecha_parto = models.DateTimeField(help_text="Fecha y hora del parto")
    es_parto_multiple = models.BooleanField(default=False, help_text="¿Es parto múltiple (gemelos, trillizos, etc)?")
    fk_clasificacion_robson = models.ForeignKey(
        CatRobson, on_delete=models.PROTECT, null=True, blank=True, 
        db_column='fk_clasificacion_robson', help_text="Clasificación de Robson"
    )
    fk_profesional_responsable = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='fk_profesional_responsable', help_text="Profesional responsable del parto")
    plan_de_parto = models.BooleanField(default=False, help_text="¿Existe plan de parto?")
    libertad_movimiento = models.BooleanField(default=False, help_text="¿Tuvo libertad de movimiento?")
    horas_trabajo_parto = models.FloatField(default=0, help_text="Horas de trabajo de parto")
    fk_acompanante = models.CharField(max_length=100, blank=True, null=True, help_text="Persona que acompaño el parto")
    fk_sala_duelo_perinatal = models.BooleanField(default=False, help_text="¿Se utilizó sala de duelo perinatal?")
    fecha_registro = models.DateTimeField(auto_now_add=True, help_text="Fecha de registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, help_text="Última actualización")
    
    class Meta:
        db_table = 'parto'
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'
        ordering = ['-fecha_parto']
    
    def __str__(self):
        return f"Parto {self.id_parto} - {self.fk_madre.nombre} - {self.fecha_parto.strftime('%Y-%m-%d')}"
    
    def tuvo_complicaciones(self):
        """Verifica si el parto tuvo complicaciones registradas."""
        return self.complicaciones.exists()


class PartoComplicacion(models.Model):
    """Modelo para registrar complicaciones durante el parto."""
    
    id_complicacion = models.AutoField(primary_key=True)
    fk_parto = models.ForeignKey(Parto, on_delete=models.CASCADE, db_column='fk_parto', related_name='complicaciones', help_text="Parto asociado")
    fk_complicacion = models.ForeignKey(CatComplicacionParto, on_delete=models.PROTECT, db_column='fk_complicacion', help_text="Tipo de complicación")
    histerectomia_obstetrica = models.BooleanField(default=False, help_text="¿Se realizó histerectomía obstétrica?")
    transfusion_sanguinea = models.BooleanField(default=False, help_text="¿Se realizó transfusión sanguínea?")
    fecha_registro = models.DateTimeField(auto_now_add=True, help_text="Fecha de registro")
    
    class Meta:
        db_table = 'parto_complicacion'
        verbose_name = 'Complicación de Parto'
        verbose_name_plural = 'Complicaciones de Parto'
        unique_together = ('fk_parto', 'fk_complicacion')
        indexes = [models.Index(fields=['fk_parto']), models.Index(fields=['fecha_registro'])]
    
    def __str__(self):
        return f"Complicación Parto {self.fk_parto.id_parto} - {self.fk_complicacion.nombre}"


class PartoAnestesia(models.Model):
    """Modelo para registrar tipo de anestesia utilizada en el parto."""
    
    TIPO_ANESTESIA_CHOICES = [
        ('ninguna', 'Sin anestesia'),
        ('local', 'Anestesia local'),
        ('epidural', 'Anestesia epidural'),
        ('raquídea', 'Anestesia raquídea'),
        ('general', 'Anestesia general'),
        ('otra', 'Otra'),
    ]
    
    id_anestesia = models.AutoField(primary_key=True)
    fk_parto = models.ForeignKey(Parto, on_delete=models.CASCADE, db_column='fk_parto', related_name='anestesias')
    tipo_anestesia = models.CharField(max_length=50, choices=TIPO_ANESTESIA_CHOICES)
    solicitada_por_paciente = models.BooleanField(default=False, help_text="¿Fue solicitada por la paciente?")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'parto_anestesia'
        verbose_name = 'Anestesia de Parto'
        verbose_name_plural = 'Anestesias de Parto'
    
    def __str__(self):
        return f"Anestesia Parto {self.fk_parto.id_parto} - {self.get_tipo_anestesia_display()}"


class IVEAtencion(models.Model):
    """Modelo para registrar atenciones de Interrupción Voluntaria del Embarazo."""
    
    CAUSAL_CHOICES = [
        ('1', 'Violación o incesto'),
        ('2', 'Peligro para la vida o salud'),
        ('3', 'Inviabilidad fetal'),
    ]
    
    id_ive_atencion = models.AutoField(primary_key=True)
    fk_madre = models.ForeignKey(MadrePaciente, on_delete=models.CASCADE, db_column='fk_madre', related_name='ive_atenciones')
    fk_causal = models.CharField(max_length=10, choices=CAUSAL_CHOICES, help_text="Causal de IVE")
    edad_gestacional_semanas = models.IntegerField(help_text="Edad gestacional en semanas")
    fecha_atencion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ive_atencion'
        verbose_name = 'Atención IVE'
        verbose_name_plural = 'Atenciones IVE'
        ordering = ['-fecha_atencion']
    
    def __str__(self):
        return f"IVE {self.id_ive_atencion} - {self.fk_madre.nombre} - Causal {self.fk_causal}"


class IVEAcompanamiento(models.Model):
    """Modelo para registrar acompañamiento profesional en IVE."""
    
    TIPO_PROFESIONAL_CHOICES = [
        ('medico', 'Médico'),
        ('psicologo', 'Psicólogo'),
        ('asistente_social', 'Asistente Social'),
        ('matrona', 'Matrona'),
        ('otro', 'Otro'),
    ]
    
    id_acomp_ive = models.AutoField(primary_key=True)
    fk_ive_atencion = models.ForeignKey(IVEAtencion, on_delete=models.CASCADE, db_column='fk_ive_atencion', related_name='acompañamientos')
    tipo_profesional = models.CharField(max_length=50, choices=TIPO_PROFESIONAL_CHOICES)
    fecha_atencion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ive_acompanamiento'
        verbose_name = 'Acompañamiento IVE'
        verbose_name_plural = 'Acompañamientos IVE'
    
    def __str__(self):
        return f"Acompañamiento IVE {self.fk_ive_atencion.id_ive_atencion} - {self.get_tipo_profesional_display()}"


class AltaAnticonceptivo(models.Model):
    """Modelo para registrar altas con métodos anticonceptivos."""
    
    TIPO_ALTA_CHOICES = [
        ('parto', 'Alta por parto'),
        ('ive', 'Alta por IVE'),
        ('otro', 'Otro motivo'),
    ]
    
    METODO_ANTICONCEPTIVO_CHOICES = [
        ('1', 'DIU'),
        ('2', 'Implante subdérmico'),
        ('3', 'Esterilización quirúrgica'),
        ('4', 'Métodos hormonales'),
        ('5', 'Otro'),
    ]
    
    id_alta_ac = models.AutoField(primary_key=True)
    fk_evento = models.IntegerField(help_text="ID del evento (parto o IVE)")
    tipo_alta = models.CharField(max_length=20, choices=TIPO_ALTA_CHOICES)
    fk_metodo_anticonceptivo = models.CharField(
        max_length=1, choices=METODO_ANTICONCEPTIVO_CHOICES, null=True, blank=True,
        help_text="Método anticonceptivo entregado"
    )
    esterilizacion_quirurgica = models.BooleanField(default=False, help_text="¿Se realizó esterilización quirúrgica?")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'alta_anticonceptivo'
        verbose_name = 'Alta con Anticonceptivo'
        verbose_name_plural = 'Altas con Anticonceptivo'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"Alta Anticonceptivo {self.id_alta_ac} - {self.get_tipo_alta_display()}"