"""
Serializers para el módulo Core con sistema RBAC nativo.
VERSIÓN NATIVA 3.0 - Noviembre 2025

Cambios principales:
- ✅ Eliminados serializers de Rol, Permiso, RolPermiso
- ✅ UsuarioSerializer usa 'groups' en lugar de 'fk_rol'
- ✅ Agregado campo 'grupos' para mostrar roles
- ✅ Agregado campo 'permisos' para debugging (opcional)
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from .models import Usuario, RestriccionTurno
from .utils import validar_run, normalizar_run
import logging

logger = logging.getLogger(__name__)


class GrupoSerializer(serializers.ModelSerializer):
    """Serializer para grupos (roles) de Django."""
    cantidad_permisos = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'cantidad_permisos']
        read_only_fields = ['id', 'cantidad_permisos']
    
    def get_cantidad_permisos(self, obj):
        """Retorna la cantidad de permisos del grupo."""
        return obj.permissions.count()


class PermisoSerializer(serializers.ModelSerializer):
    """Serializer para permisos nativos de Django."""
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'app_label', 'model']
        read_only_fields = ['id', 'name', 'codename', 'app_label', 'model']


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para Usuario con sistema RBAC nativo.
    Usa 'groups' en lugar de 'fk_rol'.
    """
    grupos = serializers.SerializerMethodField()
    grupos_ids = serializers.PrimaryKeyRelatedField(
        source='groups',
        queryset=Group.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = Usuario
        fields = [
            'id_usuario',
            'run',
            'nombre_completo',
            'email',
            'password',
            'is_active',
            'is_staff',
            'grupos',  # Read-only, para mostrar
            'grupos_ids',  # Write-only, para asignar
            'date_joined',
            'last_login',
        ]
        read_only_fields = ['id_usuario', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'email': {'required': True},
            'nombre_completo': {'required': True},
        }
    
    def get_grupos(self, obj):
        """Retorna información de los grupos (roles) del usuario."""
        return [
            {
                'id': grupo.id,
                'name': grupo.name,
            }
            for grupo in obj.groups.all()
        ]
    
    def validate_run(self, value):
        """Valida y normaliza el RUN."""
        # Si es una actualización, no validar el RUN (no se puede cambiar)
        if self.instance is not None:
            return self.instance.run
        
        # Normalizar RUN
        run_normalizado = normalizar_run(value)
        
        # Validar formato
        if not validar_run(run_normalizado):
            raise serializers.ValidationError("El RUN ingresado no es válido.")
        
        # Verificar que no exista
        if Usuario.objects.filter(run=run_normalizado).exists():
            raise serializers.ValidationError("Ya existe un usuario con este RUN.")
        
        return run_normalizado
    
    def validate_email(self, value):
        """Valida que el email sea único."""
        if self.instance and self.instance.email == value:
            return value
        
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        
        return value
    
    def create(self, validated_data):
        """Crea un usuario con los grupos asignados."""
        # Extraer password y grupos
        password = validated_data.pop('password', None)
        grupos = validated_data.pop('groups', [])
        
        # Crear usuario
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        
        # Asignar grupos
        if grupos:
            user.groups.set(grupos)
        
        logger.info(f"Usuario creado: {user.run} con grupos: {[g.name for g in grupos]}")
        
        return user
    
    def update(self, instance, validated_data):
        """Actualiza el usuario y sus grupos."""
        # Extraer password y grupos
        password = validated_data.pop('password', None)
        grupos = validated_data.pop('groups', None)
        
        # Actualizar campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar password si se proporcionó
        if password:
            instance.set_password(password)
        
        instance.save()
        
        # Actualizar grupos si se proporcionaron
        if grupos is not None:
            grupos_anteriores = set(instance.groups.values_list('id', flat=True))
            grupos_nuevos = set([g.id for g in grupos])
            
            if grupos_anteriores != grupos_nuevos:
                instance.groups.set(grupos)
                logger.info(
                    f"Grupos del usuario {instance.run} actualizados: "
                    f"{[g.name for g in grupos]}"
                )
        
        return instance


class UsuarioProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario autenticado.
    Incluye información detallada de grupos y permisos.
    """
    grupos = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id_usuario',
            'run',
            'nombre_completo',
            'email',
            'grupos',
            'permisos',
            'is_active',
            'is_staff',
            'date_joined',
            'last_login',
        ]
        read_only_fields = fields  # Todos los campos son read-only en el perfil
    
    def get_grupos(self, obj):
        """Retorna lista de grupos con sus permisos."""
        grupos_info = []
        for grupo in obj.groups.all():
            grupos_info.append({
                'id': grupo.id,
                'name': grupo.name,
                'permisos_count': grupo.permissions.count(),
            })
        return grupos_info
    
    def get_permisos(self, obj):
        """
        Retorna todos los permisos del usuario (directos + por grupos).
        Útil para debugging en frontend.
        """
        # Permisos directos
        permisos_directos = list(
            obj.user_permissions.values_list('codename', flat=True)
        )
        
        # Permisos por grupos
        permisos_grupos = set()
        for grupo in obj.groups.all():
            for permiso in grupo.permissions.all():
                permisos_grupos.add(f"{permiso.content_type.app_label}.{permiso.codename}")
        
        return {
            'permisos_directos': permisos_directos,
            'permisos_por_grupos': sorted(list(permisos_grupos)),
            'total': len(permisos_directos) + len(permisos_grupos),
        }


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para referencias en otros modelos.
    Solo información básica sin grupos ni permisos.
    """
    rol_principal = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'run', 'nombre_completo', 'email', 'rol_principal']
        read_only_fields = fields
    
    def get_rol_principal(self, obj):
        """Retorna el nombre del primer grupo asignado (rol principal)."""
        grupo = obj.groups.first()
        return grupo.name if grupo else 'Sin rol asignado'


class LoginSerializer(serializers.Serializer):
    """
    Serializer para autenticación de usuarios.
    Sin cambios respecto a la versión anterior.
    """
    run = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        run = attrs.get('run')
        password = attrs.get('password')
        
        if run and password:
            # Normalizar RUN
            try:
                run = normalizar_run(run)
            except ValueError as e:
                raise serializers.ValidationError({'run': str(e)})
            
            # Validar RUN
            if not validar_run(run):
                raise serializers.ValidationError({'run': 'RUN inválido.'})
            
            # Autenticar usuario
            user = authenticate(run=run, password=password)
            
            if not user:
                raise serializers.ValidationError(
                    {'detail': 'Credenciales inválidas.'},
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    {'detail': 'Usuario inactivo.'},
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                {'detail': 'Debe proporcionar RUN y contraseña.'},
                code='authorization'
            )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña.
    Sin cambios respecto a la versión anterior.
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {'confirm_password': 'Las contraseñas no coinciden.'}
            )
        
        # Validar longitud mínima
        if len(new_password) < 8:
            raise serializers.ValidationError(
                {'new_password': 'La contraseña debe tener al menos 8 caracteres.'}
            )
        
        return attrs


class RestriccionTurnoSerializer(serializers.ModelSerializer):
    """
    Serializer para restricciones de turno de Matronas.
    Sin cambios respecto a la versión anterior.
    """
    matrona_nombre = serializers.CharField(
        source='fk_matrona.nombre_completo',
        read_only=True
    )
    matrona_run = serializers.CharField(
        source='fk_matrona.run',
        read_only=True
    )
    es_vigente = serializers.SerializerMethodField()
    
    class Meta:
        model = RestriccionTurno
        fields = [
            'id_restriccion_turno',
            'fk_matrona',
            'matrona_nombre',
            'matrona_run',
            'turno',
            'fecha_inicio_vigencia',
            'fecha_fin_vigencia',
            'activo',
            'es_vigente',
            'observaciones',
        ]
        read_only_fields = ['id_restriccion_turno', 'es_vigente']
    
    def get_es_vigente(self, obj):
        """Retorna si la restricción está vigente actualmente."""
        return obj.es_vigente
    
    def validate(self, attrs):
        """Valida que la fecha de inicio sea anterior a la fecha de fin."""
        fecha_inicio = attrs.get('fecha_inicio_vigencia')
        fecha_fin = attrs.get('fecha_fin_vigencia')
        
        if fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError({
                'fecha_fin_vigencia': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        return attrs


class UsuarioConGruposDetalladoSerializer(serializers.ModelSerializer):
    """
    Serializer con información completa de grupos y permisos.
    Útil para administración y debugging.
    """
    grupos = GrupoSerializer(source='groups', many=True, read_only=True)
    permisos_directos = PermisoSerializer(source='user_permissions', many=True, read_only=True)
    todos_los_permisos = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id_usuario',
            'run',
            'nombre_completo',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'grupos',
            'permisos_directos',
            'todos_los_permisos',
            'date_joined',
            'last_login',
        ]
        read_only_fields = fields
    
    def get_todos_los_permisos(self, obj):
        """Retorna todos los permisos efectivos del usuario."""
        return sorted(list(obj.get_all_permissions()))


class AsignarGrupoSerializer(serializers.Serializer):
    """
    Serializer para asignar/remover grupos a usuarios.
    Útil para endpoints específicos de gestión de roles.
    """
    usuario_id = serializers.IntegerField(required=True)
    grupo_id = serializers.IntegerField(required=True)
    accion = serializers.ChoiceField(
        choices=['agregar', 'remover'],
        required=True
    )
    
    def validate_usuario_id(self, value):
        """Valida que el usuario exista."""
        try:
            Usuario.objects.get(id_usuario=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("Usuario no encontrado.")
        return value
    
    def validate_grupo_id(self, value):
        """Valida que el grupo exista."""
        try:
            Group.objects.get(id=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Grupo no encontrado.")
        return value


class CambiarRolSerializer(serializers.Serializer):
    """
    Serializer para cambiar completamente el rol de un usuario.
    Remueve todos los grupos actuales y asigna uno nuevo.
    """
    grupo_id = serializers.IntegerField(required=True)
    
    def validate_grupo_id(self, value):
        """Valida que el grupo exista."""
        try:
            Group.objects.get(id=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError("Grupo no encontrado.")
        return value
    
    def save(self, usuario):
        """Ejecuta el cambio de rol."""
        from core.rbac_utils import cambiar_grupo_usuario
        
        grupo = Group.objects.get(id=self.validated_data['grupo_id'])
        exito = cambiar_grupo_usuario(usuario, grupo.name)
        
        if not exito:
            raise serializers.ValidationError("Error al cambiar el rol del usuario.")
        
        return usuario


# ============================================================
# ESTADÍSTICAS Y REPORTES
# ============================================================

class EstadisticasUsuariosSerializer(serializers.Serializer):
    """Serializer para estadísticas de usuarios por grupo."""
    grupo = serializers.CharField()
    cantidad_usuarios = serializers.IntegerField()
    usuarios_activos = serializers.IntegerField()
    usuarios_inactivos = serializers.IntegerField()


class ResumenPermisosGrupoSerializer(serializers.Serializer):
    """Serializer para resumen de permisos de un grupo."""
    grupo_id = serializers.IntegerField()
    grupo_nombre = serializers.CharField()
    total_permisos = serializers.IntegerField()
    permisos_por_app = serializers.DictField()
    usuarios_asignados = serializers.IntegerField()