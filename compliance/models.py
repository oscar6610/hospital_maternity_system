from django.db import models
from core.models import Usuario


class TrazaMovimiento(models.Model):
    id_traza = models.AutoField(primary_key=True)
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='fk_usuario')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_accion = models.CharField(max_length=50)
    entidad_afectada = models.CharField(max_length=50)
    registro_pk_afectado = models.IntegerField()
    detalle_cambio = models.TextField()
    
    class Meta:
        db_table = 'traza_movimiento'
        verbose_name = 'Traza de Movimiento'
        verbose_name_plural = 'Trazas de Movimientos'
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"Traza {self.id_traza} - {self.tipo_accion} en {self.entidad_afectada}"