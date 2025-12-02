"""
ViewSets para el Sistema Fiori Launchpad
Integrado con JWT Authentication y RBAC
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    FioriApp,
    UserAppConfig,
    FioriAppCategory,
    FioriGroup,
    UserFioriPreferences
)
from .serializers import (
    FioriAppListSerializer,
    FioriAppDetailSerializer,
    FioriAppCreateUpdateSerializer,
    UserAppConfigSerializer,
    UserAppConfigBulkUpdateSerializer,
    FioriAppCategorySerializer,
    FioriGroupSerializer,
    UserFioriPreferencesSerializer,
    AppAccessLogSerializer,
    UserAppStatsSerializer
)
from core.rbac_utils import RBACPermission


class FioriAppViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar aplicaciones Fiori.
    
    - list: Listar apps accesibles para el usuario actual
    - retrieve: Obtener detalle de una app
    - create: Crear nueva app (solo supervisores)
    - update/partial_update: Actualizar app (solo supervisores)
    - destroy: Eliminar app (solo supervisores)
    
    Acciones personalizadas:
    - my_apps: Apps del usuario con su configuración
    - access: Registrar acceso a una app
    - statistics: Estadísticas de uso de apps
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active', 'category', 'tile_type', 'is_transactional']
    search_fields = ['title', 'subtitle', 'app_id', 'description']
    ordering_fields = ['title', 'default_order', 'created_at']
    ordering = ['default_order', 'title']
    
    def get_queryset(self):
        """
        Retorna apps disponibles según el rol del usuario.
        Supervisores ven todas, otros usuarios solo las permitidas.
        """
        user = self.request.user
        
        # Supervisores ven todas las apps
        if user.is_superuser or user.groups.filter(name='Supervisor/Jefe de Área').exists():
            return FioriApp.objects.all()
        
        # Otros usuarios solo ven apps permitidas para sus grupos
        return FioriApp.objects.filter(
            active=True
        ).filter(
            Q(allowed_groups__in=user.groups.all()) |
            Q(allowed_groups__isnull=True)  # Apps sin restricción de grupo
        ).distinct()
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return FioriAppListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FioriAppCreateUpdateSerializer
        return FioriAppDetailSerializer
    
    def get_permissions(self):
        """
        Definir permisos según la acción.
        Solo supervisores pueden crear, actualizar o eliminar apps.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Verificar permiso de supervisor
            return [IsAuthenticated(), RBACPermission()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Asignar usuario creador al crear app."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='my-apps')
    def my_apps(self, request):
        """
        Retorna apps del usuario con su configuración personalizada.
        
        GET /api/fiori/apps/my-apps/
        
        Response:
        {
            "apps": [
                {
                    "app": {...},
                    "config": {...}
                }
            ]
        }
        """
        user = request.user
        
        # Obtener apps accesibles
        accessible_apps = self.get_queryset().filter(active=True)
        
        # Obtener configuraciones del usuario
        user_configs = UserAppConfig.objects.filter(
            user=user,
            app__in=accessible_apps
        ).select_related('app', 'app__category')
        
        # Crear mapeo de configuraciones
        config_map = {config.app.id_app: config for config in user_configs}
        
        # Construir respuesta
        result = []
        for app in accessible_apps:
            app_data = FioriAppListSerializer(app, context={'request': request}).data
            config_data = None
            
            if app.id_app in config_map:
                config = config_map[app.id_app]
                config_data = {
                    'is_visible': config.is_visible,
                    'custom_order': config.custom_order,
                    'is_favorite': config.is_favorite,
                    'custom_group_name': config.custom_group_name,
                    'access_count': config.access_count,
                    'last_accessed': config.last_accessed
                }
            else:
                # Configuración por defecto si no existe
                config_data = {
                    'is_visible': True,
                    'custom_order': app.default_order,
                    'is_favorite': False,
                    'custom_group_name': '',
                    'access_count': 0,
                    'last_accessed': None
                }
            
            result.append({
                'app': app_data,
                'config': config_data
            })
        
        # Ordenar por custom_order
        result.sort(key=lambda x: x['config']['custom_order'])
        
        return Response({'apps': result})
    
    @action(detail=True, methods=['post'], url_path='access')
    def access(self, request, pk=None):
        """
        Registra el acceso del usuario a una aplicación.
        Incrementa contador y actualiza last_accessed.
        
        POST /api/fiori/apps/{id}/access/
        
        Response:
        {
            "message": "Acceso registrado",
            "access_count": 5
        }
        """
        app = self.get_object()
        user = request.user
        
        # Verificar acceso
        if not app.is_accessible_by_user(user):
            return Response(
                {'error': 'No tienes permiso para acceder a esta aplicación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Registrar acceso
        config, created = UserAppConfig.objects.get_or_create(
            user=user,
            app=app,
            defaults={'is_visible': True, 'custom_order': app.default_order}
        )
        
        config.increment_access()
        
        return Response({
            'message': 'Acceso registrado',
            'access_count': config.access_count,
            'last_accessed': config.last_accessed
        })
    
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Retorna estadísticas de uso de aplicaciones.
        
        GET /api/fiori/apps/statistics/
        
        Response: Estadísticas completas del usuario
        """
        serializer = UserAppStatsSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-category')
    def by_category(self, request):
        """
        Retorna apps agrupadas por categoría.
        
        GET /api/fiori/apps/by-category/
        
        Response:
        {
            "Maternidad": [...],
            "Neonatología": [...]
        }
        """
        apps = self.get_queryset().filter(active=True).select_related('category')
        
        # Agrupar por categoría
        categories = {}
        for app in apps:
            cat_name = app.category.name if app.category else 'Sin categoría'
            if cat_name not in categories:
                categories[cat_name] = []
            
            app_data = FioriAppListSerializer(app, context={'request': request}).data
            categories[cat_name].append(app_data)
        
        return Response(categories)


class UserAppConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar configuraciones de apps por usuario.
    
    - list: Listar configuraciones del usuario actual
    - retrieve: Obtener configuración de una app específica
    - create: Crear configuración para una app
    - update/partial_update: Actualizar configuración
    - destroy: Eliminar configuración (resetear a default)
    
    Acciones personalizadas:
    - bulk_update: Actualizar múltiples configuraciones
    - reset: Resetear configuración a valores por defecto
    """
    serializer_class = UserAppConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_visible', 'is_favorite']
    ordering_fields = ['custom_order', 'access_count', 'last_accessed']
    ordering = ['custom_order']
    
    def get_queryset(self):
        """Retorna solo configuraciones del usuario autenticado."""
        return UserAppConfig.objects.filter(
            user=self.request.user
        ).select_related('app', 'app__category')
    
    def perform_create(self, serializer):
        """Asignar usuario al crear configuración."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """
        Actualizar múltiples configuraciones de apps en una sola petición.
        
        POST /api/fiori/user-apps/bulk-update/
        
        Body:
        {
            "apps": [
                {"app_id": 1, "is_visible": true, "custom_order": 0},
                {"app_id": 2, "is_visible": false, "custom_order": 1}
            ]
        }
        """
        serializer = UserAppConfigBulkUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_count = serializer.save()
        
        return Response({
            'message': f'{updated_count} configuraciones actualizadas',
            'updated_count': updated_count
        })
    
    @action(detail=True, methods=['post'], url_path='reset')
    def reset(self, request, pk=None):
        """
        Resetear configuración de una app a valores por defecto.
        
        POST /api/fiori/user-apps/{id}/reset/
        """
        config = self.get_object()
        
        # Resetear a valores por defecto
        config.is_visible = True
        config.custom_order = config.app.default_order
        config.is_favorite = False
        config.custom_group_name = ''
        config.save()
        
        serializer = self.get_serializer(config)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='reset-all')
    def reset_all(self, request):
        """
        Resetear todas las configuraciones del usuario.
        
        POST /api/fiori/user-apps/reset-all/
        """
        configs = self.get_queryset()
        
        for config in configs:
            config.is_visible = True
            config.custom_order = config.app.default_order
            config.is_favorite = False
            config.custom_group_name = ''
        
        UserAppConfig.objects.bulk_update(
            configs,
            ['is_visible', 'custom_order', 'is_favorite', 'custom_group_name']
        )
        
        return Response({
            'message': f'{configs.count()} configuraciones reseteadas'
        })
    
    @action(detail=False, methods=['get'], url_path='favorites')
    def favorites(self, request):
        """
        Retorna solo las apps marcadas como favoritas.
        
        GET /api/fiori/user-apps/favorites/
        """
        favorites = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        """
        Retorna apps recientes (últimas accedidas).
        
        GET /api/fiori/user-apps/recent/?limit=5
        """
        limit = int(request.query_params.get('limit', 5))
        
        recent = self.get_queryset().filter(
            last_accessed__isnull=False
        ).order_by('-last_accessed')[:limit]
        
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='most-used')
    def most_used(self, request):
        """
        Retorna apps más usadas por el usuario.
        
        GET /api/fiori/user-apps/most-used/?limit=10
        """
        limit = int(request.query_params.get('limit', 10))
        
        most_used = self.get_queryset().filter(
            access_count__gt=0
        ).order_by('-access_count')[:limit]
        
        serializer = self.get_serializer(most_used, many=True)
        return Response(serializer.data)


class FioriAppCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías de aplicaciones.
    Solo supervisores pueden crear, actualizar o eliminar.
    """
    queryset = FioriAppCategory.objects.all()
    serializer_class = FioriAppCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_permissions(self):
        """Solo supervisores pueden modificar categorías."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), RBACPermission()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'], url_path='apps')
    def apps(self, request, pk=None):
        """
        Retorna todas las apps de una categoría.
        
        GET /api/fiori/categories/{id}/apps/
        """
        category = self.get_object()
        apps = category.apps.filter(active=True)
        
        # Filtrar por accesibilidad del usuario
        accessible_apps = [
            app for app in apps
            if app.is_accessible_by_user(request.user)
        ]
        
        serializer = FioriAppListSerializer(
            accessible_apps,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class FioriGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar grupos de aplicaciones.
    Permite organizar apps en secciones personalizadas.
    """
    queryset = FioriGroup.objects.all()
    serializer_class = FioriGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'name']
    ordering = ['order']
    
    def get_permissions(self):
        """Solo supervisores pueden modificar grupos."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), RBACPermission()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], url_path='add-app')
    def add_app(self, request, pk=None):
        """
        Agregar una app a un grupo.
        
        POST /api/fiori/groups/{id}/add-app/
        Body: {"app_id": 1, "order": 0}
        """
        group = self.get_object()
        app_id = request.data.get('app_id')
        order = request.data.get('order', 0)
        
        try:
            app = FioriApp.objects.get(id_app=app_id, active=True)
        except FioriApp.DoesNotExist:
            return Response(
                {'error': 'App no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Agregar app al grupo
        from .models import FioriGroupApp
        group_app, created = FioriGroupApp.objects.get_or_create(
            group=group,
            app=app,
            defaults={'order': order}
        )
        
        if not created:
            group_app.order = order
            group_app.save()
        
        return Response({
            'message': 'App agregada al grupo',
            'created': created
        })
    
    @action(detail=True, methods=['post'], url_path='remove-app')
    def remove_app(self, request, pk=None):
        """
        Remover una app de un grupo.
        
        POST /api/fiori/groups/{id}/remove-app/
        Body: {"app_id": 1}
        """
        group = self.get_object()
        app_id = request.data.get('app_id')
        
        from .models import FioriGroupApp
        deleted_count, _ = FioriGroupApp.objects.filter(
            group=group,
            app_id=app_id
        ).delete()
        
        if deleted_count > 0:
            return Response({'message': 'App removida del grupo'})
        else:
            return Response(
                {'error': 'App no encontrada en el grupo'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserFioriPreferencesViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestionar preferencias globales del usuario en el FLP.
    Solo permite retrieve y update (no list, create, delete).
    """
    serializer_class = UserFioriPreferencesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Obtiene o crea las preferencias del usuario actual."""
        user = self.request.user
        preferences, created = UserFioriPreferences.objects.get_or_create(
            user=user
        )
        return preferences
    
    def retrieve(self, request):
        """
        Obtener preferencias del usuario actual.
        
        GET /api/fiori/preferences/
        """
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    def partial_update(self, request):
        """
        Actualizar preferencias del usuario actual.
        
        PATCH /api/fiori/preferences/
        Body: {"theme": "sap_horizon", "compact_mode": true}
        """
        preferences = self.get_object()
        serializer = self.get_serializer(
            preferences,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='reset')
    def reset(self, request):
        """
        Resetear preferencias a valores por defecto.
        
        POST /api/fiori/preferences/reset/
        """
        preferences = self.get_object()
        
        # Valores por defecto
        preferences.theme = 'sap_horizon'
        preferences.tile_size_preference = '1x1'
        preferences.compact_mode = False
        preferences.group_by_category = True
        preferences.show_recent_apps = True
        preferences.recent_apps_count = 5
        preferences.enable_notifications = True
        preferences.notification_sound = False
        preferences.save()
        
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)