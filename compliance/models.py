from django.db import models
from core.models import Usuario


class TrazaMovimiento(models.Model):
    """Modelo de auditoría para registrar todas las acciones importantes del sistema."""
    TIPO_ACCION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('READ', 'Consultar'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PERMISSION_DENIED', 'Acceso Denegado'),
    ]
    
    id_traza = models.AutoField(primary_key=True)
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column='fk_usuario', related_name='trazas_movimiento')
    tipo_accion = models.CharField(max_length=20, choices=TIPO_ACCION_CHOICES, help_text="Tipo de acción realizada")
    tabla_afectada = models.CharField(max_length=100, help_text="Nombre de la tabla/modelo afectado")
    id_registro = models.IntegerField(help_text="ID del registro afectado")
    cambios_anteriores = models.JSONField(null=True, blank=True, help_text="Valores anteriores (para UPDATE/DELETE)")
    cambios_nuevos = models.JSONField(null=True, blank=True, help_text="Valores nuevos (para CREATE/UPDATE)")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="Dirección IP del cliente")
    user_agent = models.TextField(blank=True, help_text="User Agent del navegador")
    resultado = models.CharField(
        max_length=20, 
        choices=[('SUCCESS', 'Exitoso'), ('FAILED', 'Fallido')],
        default='SUCCESS'
    )
    descripcion = models.TextField(blank=True, help_text="Descripción adicional de la acción")
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'traza_movimiento'
        verbose_name = 'Traza de Movimiento'
        verbose_name_plural = 'Trazas de Movimiento'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['fk_usuario', '-fecha_hora']),
            models.Index(fields=['tabla_afectada', '-fecha_hora']),
            models.Index(fields=['tipo_accion', '-fecha_hora']),
        ]

    def __str__(self):
        return f"{self.get_tipo_accion_display()} - {self.tabla_afectada}({self.id_registro}) - {self.fk_usuario}"
