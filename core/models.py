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
    fk_rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT, db_column='fk_rol', null=True, blank=True
    )
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
    def save(self, *args, **kwargs):
        """Normaliza RUN antes de guardar siempre."""
        if self.run:
            self.run = normalizar_run(self.run)
        super().save(*args, **kwargs)
    
    # ============ NUEVOS MÉTODOS: INTEGRACIÓN CON DJANGO ============
    
    def has_perm(self, perm, obj=None):
        """
        Override para integrar RBAC custom con sistema de permisos de Django.
        
        Permite usar:
        - user.has_perm('maternity:mother:read')  ← Permisos custom
        - user.has_perm('maternity.add_madrepaciente')  ← Permisos nativos de Django
        
        Args:
            perm: Código de permiso (custom o nativo)
            obj: Objeto para permisos a nivel de objeto (opcional)
        
        Returns:
            bool: True si el usuario tiene el permiso
        """
        # Superusers tienen todos los permisos
        if self.is_active and self.is_superuser:
            return True
        
        # Si el usuario no está activo, denegar
        if not self.is_active:
            return False
        
        # Si es permiso custom (contiene ':'), usar RBAC
        if ':' in perm:
            from core.rbac_utils import tiene_permiso
            return tiene_permiso(self, perm)
        
        # Si es permiso nativo de Django, intentar mapear a custom
        codigo_custom = self._mapear_permiso_nativo(perm)
        if codigo_custom:
            from core.rbac_utils import tiene_permiso
            return tiene_permiso(self, codigo_custom)
        
        # Fallback: usar sistema nativo de Django por si acaso
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label):
        """
        Verifica si el usuario tiene permisos en un módulo específico.
        Necesario para que Django Admin funcione correctamente.
        
        Args:
            app_label: Nombre del módulo (ej: 'maternity', 'neonatology')
        
        Returns:
            bool: True si tiene al menos un permiso en ese módulo
        """
        # Superusers tienen acceso a todo
        if self.is_active and self.is_superuser:
            return True
        
        # Si no está activo, denegar
        if not self.is_active:
            return False
        
        # Verificar si tiene algún permiso del módulo en RBAC
        if self.fk_rol:
            return RolPermiso.objects.filter(
                fk_rol=self.fk_rol,
                fk_permiso__categoria=app_label,
                fk_permiso__activo=True
            ).exists()
        
        return False
    
    def _mapear_permiso_nativo(self, perm):
        """
        Mapea permisos nativos de Django a permisos custom del RBAC.
        
        Formato nativo: 'app_label.action_model' (ej: 'maternity.add_madrepaciente')
        Formato custom: 'categoria:recurso:accion' (ej: 'maternity:mother:create')
        
        Args:
            perm: Permiso nativo de Django
        
        Returns:
            str: Código de permiso custom o None si no hay mapeo
        """
        # Diccionario de mapeo: permiso_nativo → permiso_custom
        MAPEO = {
            # MATERNITY
            'maternity.add_madrepaciente': 'maternity:mother:create',
            'maternity.view_madrepaciente': 'maternity:mother:read',
            'maternity.change_madrepaciente': 'maternity:mother:update',
            'maternity.delete_madrepaciente': 'maternity:mother:update',
            
            'maternity.add_parto': 'maternity:delivery:create',
            'maternity.view_parto': 'maternity:delivery:read',
            'maternity.change_parto': 'maternity:delivery:update_all',
            'maternity.delete_parto': 'maternity:delivery:update_all',
            
            'maternity.add_partocomplicacion': 'maternity:complication:manage',
            'maternity.view_partocomplicacion': 'maternity:delivery:read',
            'maternity.change_partocomplicacion': 'maternity:complication:manage',
            'maternity.delete_partocomplicacion': 'maternity:complication:manage',
            
            'maternity.add_iveatencion': 'maternity:ive:manage',
            'maternity.view_iveatencion': 'maternity:mother:read',
            'maternity.change_iveatencion': 'maternity:ive:manage',
            'maternity.delete_iveatencion': 'maternity:ive:manage',
            
            # NEONATOLOGY
            'neonatology.add_reciennacido': 'neonatal:rn:create',
            'neonatology.view_reciennacido': 'neonatal:rn:read',
            'neonatology.change_reciennacido': 'neonatal:rn:update_immediate',
            'neonatology.delete_reciennacido': 'neonatal:rn:update_immediate',
            
            'neonatology.add_rntamizajemetabolico': 'neonatal:tamizaje:manage',
            'neonatology.view_rntamizajemetabolico': 'neonatal:rn:read',
            'neonatology.change_rntamizajemetabolico': 'neonatal:tamizaje:manage',
            
            'neonatology.add_rntamizajeauditivo': 'neonatal:tamizaje:manage',
            'neonatology.view_rntamizajeauditivo': 'neonatal:rn:read',
            'neonatology.change_rntamizajeauditivo': 'neonatal:tamizaje:manage',
            
            'neonatology.add_rntamizajecardiopatia': 'neonatal:tamizaje:manage',
            'neonatology.view_rntamizajecardiopatia': 'neonatal:rn:read',
            'neonatology.change_rntamizajecardiopatia': 'neonatal:tamizaje:manage',
            
            'neonatology.add_rnegreso': 'neonatal:discharge:manage',
            'neonatology.view_rnegreso': 'neonatal:rn:read',
            'neonatology.change_rnegreso': 'neonatal:discharge:manage',
            
            # CATALOGS
            'catalogs.add_catnacionalidad': 'catalog:manage',
            'catalogs.view_catnacionalidad': 'catalog:read',
            'catalogs.change_catnacionalidad': 'catalog:manage',
            'catalogs.delete_catnacionalidad': 'catalog:manage',
            
            # CORE
            'core.add_usuario': 'core:user:manage',
            'core.view_usuario': 'core:user:manage',
            'core.change_usuario': 'core:user:manage',
            'core.delete_usuario': 'core:user:manage',
            
            'core.add_rol': 'core:role:manage',
            'core.view_rol': 'core:role:manage',
            'core.change_rol': 'core:role:manage',
            'core.delete_rol': 'core:role:manage',
            
            # COMPLIANCE
            'compliance.view_trazamovimiento': 'compliance:audit:read',
            
            # ALERTS
            'alerts.view_alertasistema': 'alert:read',
            'alerts.change_alertasistema': 'alert:resolve',
            
            # REPORTS
            'reports.add_reporterem': 'report:generate_rem',
            'reports.view_reporterem': 'report:generate_rem',
        }
        
        return MAPEO.get(perm)
    
    # ============ FIN NUEVOS MÉTODOS ============


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