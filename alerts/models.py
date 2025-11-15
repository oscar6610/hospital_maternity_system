from django.db import models
from core.models import Usuario


class AlertaSistema(models.Model):
    id_alerta = models.AutoField(primary_key=True)
    fk_usuario_genera = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='alertas_generadas', db_column='fk_usuario_genera')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_alerta = models.CharField(max_length=50)
    nivel_gravedad = models.CharField(max_length=10)
    entidad_origen = models.CharField(max_length=50)
    resuelto = models.BooleanField(default=False)
    fk_usuario_resuelve = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='alertas_resueltas', db_column='fk_usuario_resuelve')
    
    class Meta:
        db_table = 'alerta_sistema'
        verbose_name = 'Alerta del Sistema'
        verbose_name_plural = 'Alertas del Sistema'
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"Alerta {self.id_alerta} - {self.tipo_alerta} ({self.nivel_gravedad})"