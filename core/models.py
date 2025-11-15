from django.db import models
from django.contrib.auth.hashers import make_password


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre_rol


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    run = models.CharField(max_length=15, unique=True)
    nombre_completo = models.CharField(max_length=100)
    fk_rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column='fk_rol')
    email = models.EmailField(max_length=100, unique=True)
    contrasena_hash = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.nombre_completo} ({self.run})"
    
    def save(self, *args, **kwargs):
        if not self.pk and self.contrasena_hash:
            self.contrasena_hash = make_password(self.contrasena_hash)
        super().save(*args, **kwargs)


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