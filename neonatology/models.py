from django.db import models
from maternity.models import Parto
from core.models import Usuario


class RecienNacido(models.Model):
    id_rn = models.AutoField(primary_key=True)
    fk_parto = models.ForeignKey(Parto, on_delete=models.CASCADE, db_column='fk_parto')
    sexo = models.CharField(max_length=10)
    peso_gramos = models.IntegerField()
    talla_cm = models.DecimalField(max_digits=5, decimal_places=2)
    anomalia_congenita = models.BooleanField(default=False)
    tipo_muerte = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'recien_nacido'
        verbose_name = 'Recién Nacido'
        verbose_name_plural = 'Recién Nacidos'
    
    def __str__(self):
        return f"RN {self.id_rn} - Parto {self.fk_parto.id_parto}"


class RNAtencionInmediata(models.Model):
    fk_rn = models.OneToOneField(RecienNacido, on_delete=models.CASCADE, primary_key=True, db_column='fk_rn')
    fk_profesional_registra = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='fk_profesional_registra')
    apgar_1_minuto = models.IntegerField()
    apgar_5_minutos = models.IntegerField()
    ligadura_tardia_cordon = models.BooleanField(default=False)
    contacto_piel_piel = models.CharField(max_length=50, blank=True, null=True)
    profilaxis_hepatitis_b = models.BooleanField(default=False)
    profilaxis_ocular = models.BooleanField(default=False)
    reanimacion_basica = models.BooleanField(default=False)
    reanimacion_avanzada = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'rn_atencion_inmediata'
        verbose_name = 'Atención Inmediata RN'
        verbose_name_plural = 'Atenciones Inmediatas RN'
    
    def __str__(self):
        return f"Atención Inmediata RN {self.fk_rn.id_rn}"


class RNTamizajeMetabolico(models.Model):
    id_tamizaje_metabolico = models.AutoField(primary_key=True)
    fk_rn = models.ForeignKey(RecienNacido, on_delete=models.CASCADE, db_column='fk_rn')
    fecha_muestra = models.DateField()
    es_segunda_muestra = models.BooleanField(default=False)
    resultado_alterado = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'rn_tamizaje_metabolico'
        verbose_name = 'Tamizaje Metabólico RN'
        verbose_name_plural = 'Tamizajes Metabólicos RN'
    
    def __str__(self):
        return f"Tamizaje Metabólico {self.id_tamizaje_metabolico} - RN {self.fk_rn.id_rn}"


class RNTamizajeAuditivo(models.Model):
    id_tamizaje_auditivo = models.AutoField(primary_key=True)
    fk_rn = models.ForeignKey(RecienNacido, on_delete=models.CASCADE, db_column='fk_rn')
    oido_derecho_resultado = models.CharField(max_length=10)
    oido_izquierdo_resultado = models.CharField(max_length=10)
    es_retamizaje = models.BooleanField(default=False)
    es_ambulatorio = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'rn_tamizaje_auditivo'
        verbose_name = 'Tamizaje Auditivo RN'
        verbose_name_plural = 'Tamizajes Auditivos RN'
    
    def __str__(self):
        return f"Tamizaje Auditivo {self.id_tamizaje_auditivo} - RN {self.fk_rn.id_rn}"


class RNTamizajeCardiopatia(models.Model):
    id_tamizaje_cardiopatia = models.AutoField(primary_key=True)
    fk_rn = models.ForeignKey(RecienNacido, on_delete=models.CASCADE, db_column='fk_rn')
    fecha_hora_tamizaje = models.DateTimeField()
    saturacion_mano_derecha = models.IntegerField()
    saturacion_pie = models.IntegerField()
    referido_cardiologia = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'rn_tamizaje_cardiopatia'
        verbose_name = 'Tamizaje Cardiopatía RN'
        verbose_name_plural = 'Tamizajes Cardiopatías RN'
    
    def __str__(self):
        return f"Tamizaje Cardiopatía {self.id_tamizaje_cardiopatia} - RN {self.fk_rn.id_rn}"


class RNEgreso(models.Model):
    fk_rn = models.OneToOneField(RecienNacido, on_delete=models.CASCADE, primary_key=True, db_column='fk_rn')
    tipo_alimentacion_alta = models.CharField(max_length=50)
    motivo_no_lme = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = 'rn_egreso'
        verbose_name = 'Egreso RN'
        verbose_name_plural = 'Egresos RN'
    
    def __str__(self):
        return f"Egreso RN {self.fk_rn.id_rn}"