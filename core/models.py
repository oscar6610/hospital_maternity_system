from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, run, email, password, **extra_fields):
        if not run:
            raise ValueError('El run debe ser proporcionado')
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
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nombre_rol

    def get_group(self):
        group, _ = Group.objects.get_or_create(name=self.nombre_rol)
        return group


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


class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    codigo_permiso = models.CharField(max_length=50)

    class Meta:
        db_table = 'permiso'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

    def __str__(self):
        return self.codigo_permiso


class RolPermiso(models.Model):
    fk_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='fk_rol')
    fk_permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column='fk_permiso')

    class Meta:
        db_table = 'rol_permiso'
        verbose_name = 'Rol-Permiso'
        verbose_name_plural = 'Roles-Permisos'
        unique_together = ('fk_rol', 'fk_permiso')

    def __str__(self):
        return f"{self.fk_rol.nombre_rol} - {self.fk_permiso.codigo_permiso}"