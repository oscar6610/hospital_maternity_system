"""
Django Admin para el Sistema Fiori Launchpad
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    FioriApp,
    UserAppConfig,
    FioriAppCategory,
    FioriGroup,
    FioriGroupApp,
    UserFioriPreferences
)


@admin.register(FioriAppCategory)
class FioriAppCategoryAdmin(admin.ModelAdmin):
    list_display = ['id_category', 'name', 'icon', 'order', 'active', 'apps_count', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    def apps_count(self, obj):
        return obj.apps.filter(active=True).count()
    apps_count.short_description = 'Apps Activas'


@admin.register(FioriApp)
class FioriAppAdmin(admin.ModelAdmin):
    list_display = [
        'id_app',
        'app_id',
        'title',
        'category',
        'icon_preview',
        'tile_type',
        'tile_size',
        'active',
        'is_transactional',
        'created_at'
    ]
    list_filter = [
        'active',
        'category',
        'tile_type',
        'tile_size',
        'is_transactional',
        'is_mobile_ready',
        'created_at'
    ]
    search_fields = ['app_id', 'title', 'subtitle', 'description']
    filter_horizontal = ['allowed_groups']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['default_order', 'title']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'app_id',
                'title',
                'subtitle',
                'description',
                'category'
            )
        }),
        ('Visualización', {
            'fields': (
                'icon',
                'tile_type',
                'tile_size',
                'background_color'
            )
        }),
        ('Navegación', {
            'fields': (
                'url_path',
                'module_name'
            )
        }),
        ('Control de Acceso', {
            'fields': (
                'required_permissions',
                'allowed_groups'
            )
        }),
        ('Configuración', {
            'fields': (
                'is_transactional',
                'is_mobile_ready',
                'default_order',
                'active'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def icon_preview(self, obj):
        return format_html(
            '<span style="font-size: 20px; color: var(--sap{});">📱</span>',
            obj.background_color
        )
    icon_preview.short_description = 'Icono'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserAppConfig)
class UserAppConfigAdmin(admin.ModelAdmin):
    list_display = [
        'id_config',
        'user',
        'app',
        'is_visible',
        'is_favorite',
        'custom_order',
        'access_count',
        'last_accessed'
    ]
    list_filter = [
        'is_visible',
        'is_favorite',
        'created_at',
        'last_accessed'
    ]
    search_fields = [
        'user__nombre_completo',
        'user__run',
        'app__title',
        'app__app_id'
    ]
    readonly_fields = ['access_count', 'last_accessed', 'created_at', 'updated_at']
    ordering = ['user', 'custom_order']
    
    fieldsets = (
        ('Usuario y App', {
            'fields': ('user', 'app')
        }),
        ('Configuración', {
            'fields': (
                'is_visible',
                'is_favorite',
                'custom_order',
                'custom_group_name'
            )
        }),
        ('Estadísticas de Uso', {
            'fields': (
                'access_count',
                'last_accessed'
            )
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class FioriGroupAppInline(admin.TabularInline):
    model = FioriGroupApp
    extra = 1
    autocomplete_fields = ['app']


@admin.register(FioriGroup)
class FioriGroupAdmin(admin.ModelAdmin):
    list_display = ['id_group', 'name', 'icon', 'order', 'apps_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    inlines = [FioriGroupAppInline]
    
    def apps_count(self, obj):
        return obj.apps.count()
    apps_count.short_description = 'Total Apps'


@admin.register(UserFioriPreferences)
class UserFioriPreferencesAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'theme',
        'tile_size_preference',
        'compact_mode',
        'group_by_category',
        'show_recent_apps',
        'enable_notifications'
    ]
    list_filter = [
        'theme',
        'compact_mode',
        'group_by_category',
        'show_recent_apps',
        'enable_notifications'
    ]
    search_fields = ['user__nombre_completo', 'user__run']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Visualización', {
            'fields': (
                'theme',
                'tile_size_preference',
                'compact_mode'
            )
        }),
        ('Organización', {
            'fields': (
                'group_by_category',
                'show_recent_apps',
                'recent_apps_count'
            )
        }),
        ('Notificaciones', {
            'fields': (
                'enable_notifications',
                'notification_sound'
            )
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )