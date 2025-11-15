from django.contrib import admin
from .models import Usuario, Rol, Permiso, RolPermiso

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Permiso)
admin.site.register(RolPermiso)