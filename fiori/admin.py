'''
"""
Administración Django para el Sistema Fiori Launchpad
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import FioriGroup, FioriApp, UserAppConfig, LaunchpadSettings


@admin.register(FioriGroup)
class FioriGroupAdmin(admin.ModelAdmin):
    """Administración de Grupos Fiori"""
    list_display = ('name', 'icon_display', 'order', 'apps_count', 'is_active_badge', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'icon')
        }),
        ('Visualización', {
            'fields': ('order', 'is_active')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def icon_display(self, obj):
        return format_html(
            '<i class="sap-icon--{}" style="font-size: 1.5rem;"></i>',
            obj.icon
        )
    icon_display.short_description = 'Icono'
    
    def apps_count(self, obj):
        count = obj.apps.count()
        return format_html(
            '<span style="background: #0070f2; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            count
        )
    apps_count.short_description = 'Apps'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #2da018;">✓ Activo</span>')
        return format_html('<span style="color: #c70000;">✗ Inactivo</span>')
    is_active_badge.short_description = 'Estado'


@admin.register(FioriApp)
class FioriAppAdmin(admin.ModelAdmin):
    """Administración de Aplicaciones Fiori"""
    list_display = (
        'title', 'app_id', 'group', 'app_type', 
        'icon_display', 'tile_size', 'is_active_badge', 
        'users_count'
    )
    list_filter = ('is_active', 'app_type', 'group', 'tile_size', 'created_at')
    search_fields = ('title', 'app_id', 'description')
    filter_horizontal = ('required_groups',)
    ordering = ('default_order', 'title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('app_id', 'title', 'subtitle', 'description')
        }),
        ('Clasificación', {
            'fields': ('group', 'app_type')
        }),
        ('Visualización', {
            'fields': ('icon', 'color', 'tile_size', 'default_order')
        }),
        ('Navegación', {
            'fields': ('url_path', 'url_external', 'open_in_new_tab')
        }),
        ('Permisos y Acceso', {
            'fields': ('required_permissions', 'required_groups', 'is_active')
        }),
        ('Métricas del Tile', {
            'fields': ('show_count', 'count_api_endpoint'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def icon_display(self, obj):
        colors = {
            'Accent1': '#d08014', 'Accent2': '#d04343', 'Accent3': '#db1f77',
            'Accent4': '#c0399f', 'Accent5': '#6367de', 'Accent6': '#286eb4',
            'Accent7': '#0070f2', 'Accent8': '#00a5a2', 'Accent9': '#5c8c00',
            'Accent10': '#e76500', 'Accent11': '#964806', 'Neutral': '#6c6c6c'
        }
        color = colors.get(obj.color, '#0070f2')
        return format_html(
            '<div style="background: {}; width: 40px; height: 40px; border-radius: 4px; display: flex; align-items: center; justify-content: center;">'
            '<i class="sap-icon--{}" style="color: white; font-size: 1.2rem;"></i>'
            '</div>',
            color, obj.icon
        )
    icon_display.short_description = 'Tile'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #2da018;">✓ Activa</span>')
        return format_html('<span style="color: #c70000;">✗ Inactiva</span>')
    is_active_badge.short_description = 'Estado'
    
    def users_count(self, obj):
        count = obj.user_configs.filter(is_visible=True).count()
        return format_html(
            '<span style="background: #0070f2; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            count
        )
    users_count.short_description = 'Usuarios'


@admin.register(UserAppConfig)
class UserAppConfigAdmin(admin.ModelAdmin):
    """Administración de Configuraciones de Usuario"""
    list_display = (
        'user', 'app', 'is_visible_badge', 'is_pinned_badge',
        'custom_order', 'access_count', 'last_accessed'
    )
    list_filter = ('is_visible', 'is_pinned', 'custom_group', 'created_at')
    search_fields = ('user__run', 'user__nombre_completo', 'app__title')
    readonly_fields = ('access_count', 'last_accessed', 'created_at', 'updated_at')
    ordering = ('user', 'custom_order')
    
    fieldsets = (
        ('Asignación', {
            'fields': ('user', 'app')
        }),
        ('Personalización', {
            'fields': ('is_visible', 'is_pinned', 'custom_order', 'custom_group')
        }),
        ('Métricas de Uso', {
            'fields': ('access_count', 'last_accessed'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_visible_badge(self, obj):
        if obj.is_visible:
            return format_html('<span style="color: #2da018;">✓ Visible</span>')
        return format_html('<span style="color: #6c6c6c;">✗ Oculta</span>')
    is_visible_badge.short_description = 'Visibilidad'
    
    def is_pinned_badge(self, obj):
        if obj.is_pinned:
            return format_html('<span style="color: #d08014;">★ Favorita</span>')
        return format_html('<span style="color: #d0d0d0;">☆</span>')
    is_pinned_badge.short_description = 'Favorita'


@admin.register(LaunchpadSettings)
class LaunchpadSettingsAdmin(admin.ModelAdmin):
    """Administración de Configuraciones de Launchpad"""
    list_display = ('user', 'theme', 'view_mode', 'tiles_per_row', 'show_groups', 'default_app')
    list_filter = ('theme', 'view_mode', 'show_groups')
    search_fields = ('user__run', 'user__nombre_completo')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Apariencia', {
            'fields': ('theme', 'view_mode', 'tiles_per_row')
        }),
        ('Comportamiento', {
            'fields': ('show_groups', 'default_app')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
'''