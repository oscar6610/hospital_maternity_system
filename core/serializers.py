from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Rol, Permiso, RolPermiso


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='fk_rol.nombre_rol', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id_usuario', 'run', 'nombre_completo', 'fk_rol', 'rol_nombre', 'email', 'password', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


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