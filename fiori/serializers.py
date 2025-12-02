"""
Serializers para el Sistema Fiori Launchpad
Integrado con el sistema RBAC existente
"""
from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import (
    FioriApp, 
    UserAppConfig, 
    FioriAppCategory,
    FioriGroup,
    FioriGroupApp,
    UserFioriPreferences
)
from core.models import Usuario


class FioriAppCategorySerializer(serializers.ModelSerializer):
    """Serializer para categorías de aplicaciones."""
    apps_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FioriAppCategory
        fields = [
            'id_category',
            'name',
            'description',
            'icon',
            'order',
            'active',
            'apps_count',
            'created_at'
        ]
        read_only_fields = ['id_category', 'created_at']
    
    def get_apps_count(self, obj):
        """Cantidad de apps activas en la categoría."""
        return obj.apps.filter(active=True).count()


class GroupBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para grupos (roles)."""
    
    class Meta:
        model = Group
        fields = ['id', 'name']


class FioriAppListSerializer(serializers.ModelSerializer):
    """
    Serializer para listado de aplicaciones Fiori.
    Versión optimizada sin datos anidados pesados.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    is_accessible = serializers.SerializerMethodField()
    
    class Meta:
        model = FioriApp
        fields = [
            'id_app',
            'app_id',
            'title',
            'subtitle',
            'icon',
            'tile_type',
            'tile_size',
            'background_color',
            'url_path',
            'category_name',
            'category_icon',
            'is_transactional',
            'is_mobile_ready',
            'default_order',
            'active',
            'is_accessible'
        ]
    
    def get_is_accessible(self, obj):
        """Verifica si el usuario actual puede acceder a esta app."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.is_accessible_by_user(request.user)


class FioriAppDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para una aplicación Fiori.
    Incluye información completa de categoría, grupos y permisos.
    """
    category = FioriAppCategorySerializer(read_only=True)
    allowed_groups = GroupBasicSerializer(many=True, read_only=True)
    is_accessible = serializers.SerializerMethodField()
    user_config = serializers.SerializerMethodField()
    
    class Meta:
        model = FioriApp
        fields = [
            'id_app',
            'app_id',
            'title',
            'subtitle',
            'description',
            'icon',
            'tile_type',
            'tile_size',
            'background_color',
            'url_path',
            'module_name',
            'required_permissions',
            'allowed_groups',
            'category',
            'is_transactional',
            'is_mobile_ready',
            'default_order',
            'active',
            'is_accessible',
            'user_config',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id_app', 
            'created_at', 
            'updated_at', 
            'is_accessible',
            'user_config'
        ]
    
    def get_is_accessible(self, obj):
        """Verifica si el usuario actual puede acceder."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.is_accessible_by_user(request.user)
    
    def get_user_config(self, obj):
        """Obtiene la configuración del usuario para esta app."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            config = UserAppConfig.objects.get(user=request.user, app=obj)
            return {
                'is_visible': config.is_visible,
                'custom_order': config.custom_order,
                'is_favorite': config.is_favorite,
                'custom_group_name': config.custom_group_name,
                'access_count': config.access_count,
                'last_accessed': config.last_accessed
            }
        except UserAppConfig.DoesNotExist:
            return None


class FioriAppCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar aplicaciones Fiori.
    Solo para Supervisores.
    """
    allowed_groups_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        source='allowed_groups',
        required=False
    )
    
    class Meta:
        model = FioriApp
        fields = [
            'app_id',
            'title',
            'subtitle',
            'description',
            'icon',
            'tile_type',
            'tile_size',
            'background_color',
            'url_path',
            'module_name',
            'required_permissions',
            'allowed_groups_ids',
            'category',
            'is_transactional',
            'is_mobile_ready',
            'default_order',
            'active'
        ]
    
    def validate_app_id(self, value):
        """Valida que el app_id sea único."""
        instance = self.instance
        if instance:
            # Si es actualización, excluir la instancia actual
            if FioriApp.objects.exclude(pk=instance.pk).filter(app_id=value).exists():
                raise serializers.ValidationError("Ya existe una app con este app_id")
        else:
            # Si es creación nueva
            if FioriApp.objects.filter(app_id=value).exists():
                raise serializers.ValidationError("Ya existe una app con este app_id")
        return value
    
    def validate_url_path(self, value):
        """Valida que la URL comience con /fiori/."""
        if not value.startswith('/fiori/'):
            raise serializers.ValidationError("La URL debe comenzar con /fiori/")
        return value
    
    def create(self, validated_data):
        """Crear app y asignar usuario creador."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class UserAppConfigSerializer(serializers.ModelSerializer):
    """
    Serializer para la configuración de apps por usuario.
    """
    app_detail = FioriAppListSerializer(source='app', read_only=True)
    app_id = serializers.PrimaryKeyRelatedField(
        queryset=FioriApp.objects.filter(active=True),
        source='app',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = UserAppConfig
        fields = [
            'id_config',
            'app_detail',
            'app_id',
            'is_visible',
            'custom_order',
            'is_favorite',
            'custom_group_name',
            'access_count',
            'last_accessed',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id_config',
            'access_count',
            'last_accessed',
            'created_at',
            'updated_at'
        ]
    
    def create(self, validated_data):
        """Crear configuración para el usuario autenticado."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        """Validar que el usuario no tenga ya configuración para esta app."""
        request = self.context.get('request')
        app = data.get('app')
        
        if not self.instance:  # Solo en creación
            if UserAppConfig.objects.filter(user=request.user, app=app).exists():
                raise serializers.ValidationError(
                    "Ya existe una configuración para esta app"
                )
        
        return data


class UserAppConfigBulkUpdateSerializer(serializers.Serializer):
    """
    Serializer para actualización masiva de configuraciones de apps.
    """
    apps = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="Lista de apps con sus configuraciones"
    )
    
    def validate_apps(self, value):
        """Validar estructura de cada app."""
        for app_data in value:
            if 'app_id' not in app_data:
                raise serializers.ValidationError("Cada app debe tener 'app_id'")
            
            # Validar que app_id exista
            if not FioriApp.objects.filter(
                id_app=app_data['app_id'],
                active=True
            ).exists():
                raise serializers.ValidationError(
                    f"App con id {app_data['app_id']} no existe o está inactiva"
                )
        
        return value
    
    def save(self):
        """Actualizar configuraciones masivamente."""
        user = self.context['request'].user
        apps_data = self.validated_data['apps']
        
        updated_count = 0
        for app_data in apps_data:
            app = FioriApp.objects.get(id_app=app_data['app_id'])
            
            config, created = UserAppConfig.objects.get_or_create(
                user=user,
                app=app,
                defaults={
                    'is_visible': app_data.get('is_visible', True),
                    'custom_order': app_data.get('custom_order', 0),
                    'is_favorite': app_data.get('is_favorite', False)
                }
            )
            
            if not created:
                # Actualizar solo campos proporcionados
                if 'is_visible' in app_data:
                    config.is_visible = app_data['is_visible']
                if 'custom_order' in app_data:
                    config.custom_order = app_data['custom_order']
                if 'is_favorite' in app_data:
                    config.is_favorite = app_data['is_favorite']
                if 'custom_group_name' in app_data:
                    config.custom_group_name = app_data['custom_group_name']
                
                config.save()
            
            updated_count += 1
        
        return updated_count


class UserFioriPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer para preferencias globales del usuario en el FLP.
    """
    user_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserFioriPreferences
        fields = [
            'theme',
            'tile_size_preference',
            'compact_mode',
            'group_by_category',
            'show_recent_apps',
            'recent_apps_count',
            'enable_notifications',
            'notification_sound',
            'user_info',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """Información básica del usuario."""
        return {
            'id_usuario': obj.user.id_usuario,
            'nombre_completo': obj.user.nombre_completo,
            'run': obj.user.run
        }


class FioriGroupAppSerializer(serializers.ModelSerializer):
    """Serializer para la relación entre grupos y apps."""
    app_detail = FioriAppListSerializer(source='app', read_only=True)
    
    class Meta:
        model = FioriGroupApp
        fields = ['app', 'app_detail', 'order']


class FioriGroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos de aplicaciones."""
    apps_count = serializers.SerializerMethodField()
    apps_detail = FioriGroupAppSerializer(
        source='fiorig roupapp_set',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = FioriGroup
        fields = [
            'id_group',
            'name',
            'description',
            'icon',
            'order',
            'is_collapsible',
            'collapsed_by_default',
            'apps_count',
            'apps_detail',
            'created_at'
        ]
        read_only_fields = ['id_group', 'created_at']
    
    def get_apps_count(self, obj):
        """Cantidad de apps en el grupo."""
        return obj.apps.filter(active=True).count()


class AppAccessLogSerializer(serializers.Serializer):
    """
    Serializer para registrar accesos a una aplicación.
    No es un ModelSerializer porque solo registra el acceso.
    """
    app_id = serializers.IntegerField(required=True)
    
    def validate_app_id(self, value):
        """Validar que la app exista."""
        try:
            FioriApp.objects.get(id_app=value, active=True)
        except FioriApp.DoesNotExist:
            raise serializers.ValidationError("App no encontrada o inactiva")
        return value
    
    def save(self):
        """Registrar el acceso."""
        user = self.context['request'].user
        app = FioriApp.objects.get(id_app=self.validated_data['app_id'])
        
        # Obtener o crear configuración
        config, created = UserAppConfig.objects.get_or_create(
            user=user,
            app=app,
            defaults={'is_visible': True, 'custom_order': 0}
        )
        
        # Incrementar contador de accesos
        config.increment_access()
        
        return config


class UserAppStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de uso de apps por usuario.
    """
    total_apps_available = serializers.IntegerField()
    total_apps_visible = serializers.IntegerField()
    total_apps_favorite = serializers.IntegerField()
    most_used_apps = serializers.ListField(
        child=serializers.DictField()
    )
    recent_apps = serializers.ListField(
        child=serializers.DictField()
    )
    apps_by_category = serializers.DictField()
    
    def to_representation(self, instance):
        """
        Generar estadísticas del usuario.
        instance debe ser un Usuario.
        """
        user = instance
        
        # Apps disponibles para el usuario
        available_apps = FioriApp.objects.filter(
            active=True
        ).filter(
            allowed_groups__in=user.groups.all()
        ).distinct()
        
        # Configuraciones del usuario
        user_configs = UserAppConfig.objects.filter(user=user)
        
        # Apps más usadas
        most_used = user_configs.filter(
            access_count__gt=0
        ).order_by('-access_count')[:5]
        
        most_used_data = [
            {
                'app_id': config.app.id_app,
                'title': config.app.title,
                'icon': config.app.icon,
                'access_count': config.access_count,
                'last_accessed': config.last_accessed
            }
            for config in most_used
        ]
        
        # Apps recientes
        recent = user_configs.filter(
            last_accessed__isnull=False
        ).order_by('-last_accessed')[:5]
        
        recent_data = [
            {
                'app_id': config.app.id_app,
                'title': config.app.title,
                'icon': config.app.icon,
                'last_accessed': config.last_accessed
            }
            for config in recent
        ]
        
        # Apps por categoría
        apps_by_cat = {}
        for app in available_apps:
            cat_name = app.category.name if app.category else 'Sin categoría'
            if cat_name not in apps_by_cat:
                apps_by_cat[cat_name] = 0
            apps_by_cat[cat_name] += 1
        
        return {
            'total_apps_available': available_apps.count(),
            'total_apps_visible': user_configs.filter(is_visible=True).count(),
            'total_apps_favorite': user_configs.filter(is_favorite=True).count(),
            'most_used_apps': most_used_data,
            'recent_apps': recent_data,
            'apps_by_category': apps_by_cat
        }