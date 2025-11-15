from django.db import models
from core.models import Usuario


class ReporteREM(models.Model):
    id_reporte = models.AutoField(primary_key=True)
    fk_usuario_genera = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='fk_usuario_genera')
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    tipo_reporte = models.CharField(max_length=50)
    rango_fecha_inicio = models.DateField()
    rango_fecha_fin = models.DateField()
    estado = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'reporte_rem'
        verbose_name = 'Reporte REM'
        verbose_name_plural = 'Reportes REM'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Reporte {self.id_reporte} - {self.tipo_reporte} ({self.estado})"


class ReporteREMDetalle(models.Model):
    fk_reporte = models.ForeignKey(ReporteREM, on_delete=models.CASCADE, db_column='fk_reporte')
    nombre_variable_rem = models.CharField(max_length=100)
    valor_reportado = models.IntegerField()
    
    class Meta:
        db_table = 'reporte_rem_detalle'
        verbose_name = 'Detalle Reporte REM'
        verbose_name_plural = 'Detalles Reportes REM'
        unique_together = ('fk_reporte', 'nombre_variable_rem')
    
    def __str__(self):
        return f"Detalle Reporte {self.fk_reporte.id_reporte} - {self.nombre_variable_rem}"