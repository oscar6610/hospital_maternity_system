from django.contrib import admin
from .models import RecienNacido, RNAtencionInmediata, RNTamizajeMetabolico, RNTamizajeAuditivo, RNTamizajeCardiopatia, RNEgreso

admin.site.register(RecienNacido)
admin.site.register(RNAtencionInmediata)
admin.site.register(RNTamizajeMetabolico)
admin.site.register(RNTamizajeAuditivo)
admin.site.register(RNTamizajeCardiopatia)
admin.site.register(RNEgreso)