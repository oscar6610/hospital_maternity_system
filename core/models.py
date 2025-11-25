from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from .utils import validar_run, normalizar_run


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, run, email, password, **extra_fields):
        if not run:
            raise ValueError('El run debe ser proporcionado')
        # Validar formato y dígito verificador del RUN antes de crear
        if not validar_run(run):
            raise ValueError('El run proporcionado no es válido')
        email = self.normalize_email(email)
        user = self.model(run=run, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, run, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(run, email, password, **extra_fields)

    def create_superuser(self, run, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(run, email, password, **extra_fields)


class Usuario(AbstractUser):
    username = None
    id_usuario = models.AutoField(primary_key=True)
    run = models.CharField(max_length=15, unique=True)
    nombre_completo = models.CharField(max_length=100)
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'run'
    REQUIRED_FIELDS = ['email', 'nombre_completo']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        permissions = [
            ("can_manage_all_users", "Puede gestionar todos los usuarios"),
            ("can_view_audit_logs", "Puede ver logs de auditoría"),
        ]
    
    def __str__(self):
        return f"{self.nombre_completo} ({self.run})"

    def clean(self):
        """Normaliza y valida RUN antes de cualquier operación."""

        if self.run:
            try:
                # Intentar normalizar el RUN
                self.run = normalizar_run(self.run)
            except ValueError as e:
                # Capturar el ValueError y convertirlo en ValidationError
                raise ValidationError({'run': str(e)})

            # Validar el RUN normalizado
            if not validar_run(self.run):
                raise ValidationError({'run': 'El run ingresado no es válido.'})

        super().clean()

    def save(self, *args, **kwargs):
        """Normaliza RUN antes de guardar siempre."""
        if self.run:
            self.run = normalizar_run(self.run)
        super().save(*args, **kwargs)
    

class RestriccionTurno(models.Model):
    """Modelo para restringir el acceso de Matronas a registros de su turno específico."""
    id_restriccion = models.AutoField(primary_key=True)
    fk_matrona = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        db_column='fk_matrona',
        related_name='restriccion_turno',
        limit_choices_to={'fk_rol__nombre_rol': 'matrona_clinica'}
    )
    turno = models.CharField(
        max_length=20,
        choices=[
            ('MATUTINO', 'Turno Matutino (08:00-16:00)'),
            ('VESPERTINO', 'Turno Vespertino (16:00-00:00)'),
            ('NOCTURNO', 'Turno Nocturno (00:00-08:00)'),
        ],
        help_text="Turno asignado a la matrona"
    )
    fecha_inicio = models.DateField(help_text="Fecha de inicio del turno")
    fecha_fin = models.DateField(null=True, blank=True, help_text="Fecha de fin del turno (null = indefinido)")
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restriccion_turno'
        verbose_name = 'Restricción de Turno'
        verbose_name_plural = 'Restricciones de Turno'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.fk_matrona.nombre_completo} - {self.get_turno_display()}"
    
    @property
    def es_vigente(self):
        """Verifica si la restricción de turno está vigente."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.activo and self.fecha_inicio <= today and (self.fecha_fin is None or today <= self.fecha_fin)