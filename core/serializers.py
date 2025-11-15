from rest_framework import serializers
from .models import Usuario, Rol, Permiso, RolPermiso


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='fk_rol.nombre_rol', read_only=True)
    
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'run', 'nombre_completo', 'fk_rol', 'rol_nombre', 'email', 'contrasena_hash', 'activo']
        extra_kwargs = {
            'contrasena_hash': {'write_only': True}
        }


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = '__all__'


class RolPermisoSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='fk_rol.nombre_rol', read_only=True)
    permiso_codigo = serializers.CharField(source='fk_permiso.codigo_permiso', read_only=True)
    
    class Meta:
        model = RolPermiso
        fields = ['id', 'fk_rol', 'rol_nombre', 'fk_permiso', 'permiso_codigo']