from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario, Rol, Permiso, RolPermiso


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
			'fields': ('run', 'email', 'nombre_completo', 'password1', 'password2'),
		}),
	)
	list_display = ('run', 'email', 'nombre_completo', 'is_staff')
	search_fields = ('run', 'email', 'nombre_completo')
	ordering = ('run',)


admin.site.register(Rol)
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Permiso)
admin.site.register(RolPermiso)