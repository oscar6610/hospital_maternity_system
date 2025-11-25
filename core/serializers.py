from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario
from .utils import validar_run, normalizar_run



class UsuarioSerializer(serializers.ModelSerializer):
    grupo = serializers.SerializerMethodField()
    password = serializers.CharField(
        write_only=True,
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'run', 'nombre_completo',
            'email', 'password', 'is_active', 'date_joined', 'grupo',
        ]

        read_only_fields = ['is_active', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'run': {'required': True}
        }
    def get_grupo(self, obj):
        grupos = obj.groups.all()
        if grupos.exists():
            return [g.name for g in grupos]  # si quieres lista
            # return grupos.first().name      # si quieres solo uno
        return None

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
    grupo = serializers.SerializerMethodField()
    
    def get_grupo(self, obj):
            grupos = obj.groups.all()
            if grupos.exists():
                return [g.name for g in grupos]
            return None
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'run', 'nombre_completo', 'email', 'is_active', 'date_joined', 'grupo']
        read_only_fields = ['id_usuario', 'run', 'is_active', 'date_joined', 'grupo']