from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from .utils import validar_run


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


class Rol(models.Model):
    """Modelo para roles del sistema con control de acceso basado en roles (RBAC)."""
    ROLES_CHOICES = [
        ('matrona_clinica', 'Matrona Clínica'),
        ('supervisor_jefe', 'Supervisor/Jefe de Área'),
        ('medico', 'Médico(a)'),
        ('enfermero', 'Enfermero(a)'),
        ('administrativo', 'Administrativo(a)'),
    ]
    
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True, choices=ROLES_CHOICES)
    descripcion = models.TextField(blank=True, help_text="Descripción del rol y responsabilidades")
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre_rol']

    def __str__(self):
        return dict(self.ROLES_CHOICES).get(self.nombre_rol, self.nombre_rol)

    def get_group(self):
        group, _ = Group.objects.get_or_create(name=self.nombre_rol)
        return group
    
    def get_permisos(self):
        """Obtiene todos los permisos asociados a este rol."""
        return Permiso.objects.filter(rolpermiso__fk_rol=self).distinct()



class Usuario(AbstractUser):
    username = None
    id_usuario = models.AutoField(primary_key=True)
    run = models.CharField(max_length=15, unique=True)
    nombre_completo = models.CharField(max_length=100)
    fk_rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column='fk_rol', null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'run'
    REQUIRED_FIELDS = ['email', 'nombre_completo']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre_completo} ({self.run})"

    def clean(self):
        """Validación a nivel de modelo para asegurar RUN válido en admin y forms."""
        if self.run and not validar_run(self.run):
            raise ValidationError({'run': 'El run ingresado no es válido.'})


class Permiso(models.Model):
    """Modelo para permisos granulares del sistema RBAC."""
    CATEGORIA_CHOICES = [
        ('catalog', 'Catálogos'),
        ('maternity', 'Maternidad'),
        ('neonatology', 'Neonatología'),
        ('reports', 'Reportes'),
        ('alerts', 'Alertas'),
        ('compliance', 'Cumplimiento'),
        ('core', 'Core/Usuarios'),
    ]
    
    id_permiso = models.AutoField(primary_key=True)
    codigo_permiso = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Código único del permiso ej: maternity:mother:create"
    )
    nombre_permiso = models.CharField(max_length=150, help_text="Nombre legible del permiso")
    descripcion = models.TextField(help_text="Descripción detallada del permiso")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'permiso'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['categoria', 'codigo_permiso']
        indexes = [
            models.Index(fields=['codigo_permiso']),
            models.Index(fields=['categoria']),
        ]

    def __str__(self):
        return f"{self.codigo_permiso} - {self.nombre_permiso}"


class RolPermiso(models.Model):
    """Asociación entre Roles y Permisos para control de acceso granular."""
    fk_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='fk_rol', related_name='permisos')
    fk_permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column='fk_permiso', related_name='roles')
    fecha_asignacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'rol_permiso'
        verbose_name = 'Rol-Permiso'
        verbose_name_plural = 'Roles-Permisos'
        unique_together = ('fk_rol', 'fk_permiso')
        ordering = ['fk_rol', 'fk_permiso']

    def __str__(self):
        return f"{self.fk_rol.nombre_rol} - {self.fk_permiso.codigo_permiso}"


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