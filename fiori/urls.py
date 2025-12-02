"""
URLs del Sistema Fiori Launchpad
Incluye vistas HTML y API REST
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .viewsets import (
    FioriAppViewSet,
    UserAppConfigViewSet,
    FioriAppCategoryViewSet,
    FioriGroupViewSet,
    UserFioriPreferencesViewSet
)

# Router para la API REST
router = DefaultRouter()
router.register(r'apps', FioriAppViewSet, basename='fiori-app')
router.register(r'user-apps', UserAppConfigViewSet, basename='user-app-config')
router.register(r'categories', FioriAppCategoryViewSet, basename='fiori-category')
router.register(r'groups', FioriGroupViewSet, basename='fiori-group')

app_name = 'fiori'

urlpatterns = [
    # ==========================================
    # VISTAS HTML (Templates)
    # ==========================================
    
    # Launchpad Principal
    path('', views.launchpad, name='launchpad'),
    
    # Personalización
    path('personalizar/', views.app_personalizer, name='personalizer'),
    
    # Apps de Maternidad
    path('madres/', include('fiori.madres.urls', namespace='madres')),
    path('partos/', include('fiori.partos.urls', namespace='partos')),
    
    # Apps de Neonatología
    path('neonatologia/', include('fiori.neonatologia.urls', namespace='neonatologia')),
    
    # Apps de Reportes (Solo Supervisores)
    path('reportes/', include('fiori.reportes.urls', namespace='reportes')),
    
    # Apps de Auditoría (Solo Supervisores)
    path('auditoria/', include('fiori.auditoria.urls', namespace='auditoria')),
    
    # Apps de Usuarios (Solo Supervisores)
    path('usuarios/', include('fiori.usuarios.urls', namespace='usuarios')),
    
    # ==========================================
    # API REST
    # ==========================================
    
    # API de aplicaciones, configuraciones, categorías y grupos
    path('api/', include(router.urls)),
    
    # API de preferencias del usuario
    path('api/preferences/', UserFioriPreferencesViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update'
    }), name='user-preferences'),
    
    path('api/preferences/reset/', UserFioriPreferencesViewSet.as_view({
        'post': 'reset'
    }), name='user-preferences-reset'),
]