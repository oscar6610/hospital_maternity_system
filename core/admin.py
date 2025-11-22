from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Usuario, Rol, Permiso, RolPermiso, RestriccionTurno
from compliance.models import TrazaMovimiento


class UsuarioAdmin(DjangoUserAdmin):
	fieldsets = (
		(None, {'fields': ('run', 'password')}),
		(_('Personal info'), {'fields': ('nombre_completo', 'email', 'fk_rol')}),
		(_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		(_('Important dates'), {'fields': ('last_login', 'date_joined')}),
	)
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('run', 'email', 'nombre_completo', 'fk_rol', 'password1', 'password2'),
		}),
	)
	list_display = ('run', 'email', 'nombre_completo', 'fk_rol', 'is_staff', 'is_active')
	list_filter = ('fk_rol', 'is_active', 'is_staff')
	search_fields = ('run', 'email', 'nombre_completo')
	ordering = ('run',)


class RolAdmin(admin.ModelAdmin):
	list_display = ('id_rol', 'nombre_rol', 'descripcion_corta', 'cantidad_permisos', 'fecha_creacion')
	search_fields = ('nombre_rol', 'descripcion')
	readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
	fieldsets = (
		('Información General', {'fields': ('nombre_rol', 'descripcion')}),
		('Auditoría', {'fields': ('fecha_creacion', 'fecha_actualizacion'), 'classes': ('collapse',)})
	)
	
	def descripcion_corta(self, obj):
		return obj.descripcion[:80] + '...' if len(obj.descripcion) > 80 else obj.descripcion
	descripcion_corta.short_description = 'Descripción'
	
	def cantidad_permisos(self, obj):
		return obj.permisos.count()
	cantidad_permisos.short_description = 'Permisos'


class PermisoAdmin(admin.ModelAdmin):
	list_display = ('codigo_permiso', 'nombre_permiso', 'categoria_badge', 'activo', 'fecha_creacion')
	list_filter = ('categoria', 'activo', 'fecha_creacion')
	search_fields = ('codigo_permiso', 'nombre_permiso', 'descripcion')
	readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
	fieldsets = (
		('Información General', {'fields': ('codigo_permiso', 'nombre_permiso', 'descripcion', 'categoria', 'activo')}),
		('Auditoría', {'fields': ('fecha_creacion', 'fecha_actualizacion'), 'classes': ('collapse',)}),
	)
	
	def categoria_badge(self, obj):
		colores = {
			'catalog': '#17a2b8',
			'maternity': '#28a745',
			'neonatology': '#ffc107',
			'reports': '#007bff',
			'alerts': '#dc3545',
			'compliance': '#6f42c1',
			'core': '#6c757d',
		}
		color = colores.get(obj.categoria, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
			color,
			obj.get_categoria_display()
		)
	categoria_badge.short_description = 'Categoría'


class RolPermisoInline(admin.TabularInline):
	model = RolPermiso
	extra = 1
	fields = ('fk_permiso', 'fecha_asignacion')
	readonly_fields = ('fecha_asignacion',)


class RolPermisoAdmin(admin.ModelAdmin):
	list_display = ('fk_rol', 'fk_permiso', 'categoria_permiso', 'fecha_asignacion')
	list_filter = ('fk_rol', 'fk_permiso__categoria', 'fecha_asignacion')
	search_fields = ('fk_rol__nombre_rol', 'fk_permiso__codigo_permiso')
	readonly_fields = ('fecha_asignacion',)
	fieldsets = (
		('Asignación', {'fields': ('fk_rol', 'fk_permiso')}),
		('Auditoría', {'fields': ('fecha_asignacion',), 'classes': ('collapse',)}),
	)
	
	def categoria_permiso(self, obj):
		return obj.fk_permiso.get_categoria_display()
	categoria_permiso.short_description = 'Categoría'


class TrazaMovimientoAdmin(admin.ModelAdmin):
	list_display = ('id_traza', 'tipo_accion_badge', 'tabla_afectada', 'fk_usuario', 'resultado_badge', 'fecha_hora')
	list_filter = ('tipo_accion', 'resultado', 'tabla_afectada', 'fecha_hora')
	search_fields = ('fk_usuario__nombre_completo', 'tabla_afectada', 'descripcion')
	readonly_fields = ('id_traza', 'fecha_hora', 'cambios_anteriores', 'cambios_nuevos')
	date_hierarchy = 'fecha_hora'
	
	fieldsets = (
		('Información de la Acción', {
			'fields': ('id_traza', 'fk_usuario', 'tipo_accion', 'resultado', 'descripcion')
		}),
		('Detalles de Afectación', {
			'fields': ('tabla_afectada', 'id_registro')
		}),
		('Cambios', {
			'fields': ('cambios_anteriores', 'cambios_nuevos'),
			'classes': ('collapse',)
		}),
		('Red', {
			'fields': ('ip_address', 'user_agent'),
			'classes': ('collapse',)
		}),
		('Auditoría', {
			'fields': ('fecha_hora',),
			'classes': ('collapse',)
		}),
	)
	
	def tipo_accion_badge(self, obj):
		colores = {
			'CREATE': '#28a745',
			'UPDATE': '#ffc107',
			'DELETE': '#dc3545',
			'READ': '#17a2b8',
			'LOGIN': '#007bff',
			'LOGOUT': '#6c757d',
			'PERMISSION_DENIED': '#dc3545',
		}
		color = colores.get(obj.tipo_accion, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
			color,
			obj.get_tipo_accion_display()
		)
	tipo_accion_badge.short_description = 'Tipo de Acción'
	
	def resultado_badge(self, obj):
		color = '#28a745' if obj.resultado == 'SUCCESS' else '#dc3545'
		return format_html(
			'<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
			color,
			obj.get_resultado_display()
		)
	resultado_badge.short_description = 'Resultado'
	
	def has_add_permission(self, request):
		"""No permitir agregar trazas manualmente"""
		return False
	
	def has_delete_permission(self, request, obj=None):
		"""No permitir eliminar trazas"""
		return False


class RestriccionTurnoAdmin(admin.ModelAdmin):
	list_display = ('fk_matrona', 'turno_display', 'fecha_inicio', 'fecha_fin', 'activo', 'es_vigente_badge')
	list_filter = ('turno', 'activo', 'fecha_inicio')
	search_fields = ('fk_matrona__nombre_completo', 'fk_matrona__run')
	readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
	fieldsets = (
		('Asignación de Turno', {
			'fields': ('fk_matrona', 'turno', 'fecha_inicio', 'fecha_fin', 'activo')
		}),
		('Observaciones', {
			'fields': ('observaciones',)
		}),
		('Auditoría', {
			'fields': ('fecha_creacion', 'fecha_actualizacion'),
			'classes': ('collapse',)
		}),
	)
	
	def turno_display(self, obj):
		colores = {
			'MATUTINO': '#28a745',
			'VESPERTINO': '#ffc107',
			'NOCTURNO': '#17a2b8',
		}
		color = colores.get(obj.turno, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
			color,
			obj.get_turno_display()
		)
	turno_display.short_description = 'Turno'
	
	def es_vigente_badge(self, obj):
		if obj.es_vigente:
			return format_html(
				'<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">Vigente</span>'
			)
		else:
			return format_html(
				'<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">No vigente</span>'
			)
	es_vigente_badge.short_description = 'Estado'


# Registrar modelos
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Rol, RolAdmin)
admin.site.register(Permiso, PermisoAdmin)
admin.site.register(RolPermiso, RolPermisoAdmin)
admin.site.register(TrazaMovimiento, TrazaMovimientoAdmin)
admin.site.register(RestriccionTurno, RestriccionTurnoAdmin)
