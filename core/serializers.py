from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Rol, Permiso, RolPermiso
from .utils import validar_run, normalizar_run



class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='fk_rol.nombre_rol', read_only=True)
    password = serializers.CharField(
        write_only=True,
        required=True, 
        style={'input_type': 'password'}
    )
    fk_rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        required=True,
    )

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'run', 'nombre_completo', 'fk_rol', 'rol_nombre',
            'email', 'password', 'is_active'
        ]
        read_only_fields = ['rol_nombre', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'fk_rol': {'required': True},
            'run': {'required': True}
        }

    def validate_run(self, value):
        """
        Normaliza el RUN, valida dígito verificador y evita duplicados.
        """
        # Si es una actualización, retornar el valor actual
        if self.instance is not None:
            return self.instance.run
            
        # Normalizar RUN a formato estándar
        run_normalizado = normalizar_run(value)

        # Validar matemáticamente
        if not validar_run(run_normalizado):
            raise serializers.ValidationError("El RUN ingresado no es válido.")

        # Verificar duplicados
        if Usuario.objects.filter(run=run_normalizado).exists():
            raise serializers.ValidationError("Este RUN ya está registrado.")

        return run_normalizado

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """
        Actualización controlada de usuarios.
        
        Reglas:
        - RUN nunca se puede cambiar (ya validado)
        - Password no se cambia aquí (usar change_password endpoint)
        - Rol solo lo puede cambiar quien tenga 'core:user:manage'
        - Otros campos: solo nombre_completo y email
        """
        # Obtener el request del contexto
        request = self.context.get('request')
        
        # VALIDACIÓN: Cambio de rol requiere permiso especial
        if 'fk_rol' in validated_data:
            # Importar aquí para evitar dependencias circulares
            from core.rbac_utils import tiene_permiso
            
            # Verificar si el usuario tiene permiso para gestionar usuarios
            if not tiene_permiso(request.user, 'core:user:manage'):
                raise serializers.ValidationError({
                    'fk_rol': 'No tienes permiso para cambiar roles de usuario. Se requiere: core:user:manage'
                })
            
            # Si está cambiando su propio rol, advertir pero permitir (para superusers)
            if instance.id_usuario == request.user.id_usuario and not request.user.is_superuser:
                raise serializers.ValidationError({
                    'fk_rol': 'No puedes cambiar tu propio rol'
                })
        else:
            # Si NO viene fk_rol en la petición, removerlo de validated_data
            validated_data.pop('fk_rol', None)
        
        # Remover campos que NUNCA deben actualizarse aquí
        validated_data.pop('run', None)  # RUN es inmutable
        validated_data.pop('password', None)  # Password tiene su propio endpoint
        validated_data.pop('is_active', None)  # is_active requiere permiso especial
        validated_data.pop('is_staff', None)  # is_staff requiere permiso especial
        validated_data.pop('is_superuser', None)  # is_superuser solo admin puede cambiar
        
        # Campos permitidos para actualización normal
        allowed_fields = {'nombre_completo', 'email', 'fk_rol'}
        
        # Remover campos no permitidos
        for field in list(validated_data.keys()):
            if field not in allowed_fields:
                validated_data.pop(field, None)
        
        # Ejecutar actualización
        return super().update(instance, validated_data)


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


class LoginSerializer(serializers.Serializer):
    run = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        run = data.get('run')
        password = data.get('password')
        
        if not run or not password:
            raise serializers.ValidationError('run y password son requeridos')
        
        user = authenticate(username=run, password=password)
        if not user:
            raise serializers.ValidationError('Credenciales inválidas')
        
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError('Las nuevas contraseñas no coinciden')
        if len(data['new_password']) < 8:
            raise serializers.ValidationError('La contraseña debe tener al menos 8 caracteres')
        return data


class UsuarioProfileSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='fk_rol.nombre_rol', read_only=True)
    
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'run', 'nombre_completo', 'email', 'fk_rol', 'rol_nombre', 'is_active', 'date_joined']
        read_only_fields = ['id_usuario', 'run', 'is_active', 'date_joined']