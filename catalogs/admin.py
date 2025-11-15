from django.contrib import admin
from .models import CatNacionalidad, CatPuebloOriginario, CatComplicacionParto, CatRobson, CatTipoParto

admin.site.register(CatNacionalidad)
admin.site.register(CatPuebloOriginario)
admin.site.register(CatComplicacionParto)
admin.site.register(CatRobson)
admin.site.register(CatTipoParto)