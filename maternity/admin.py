from django.contrib import admin
from .models import MadrePaciente, Embarazo, Parto, PartoComplicacion, PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo

admin.site.register(MadrePaciente)
admin.site.register(Embarazo)
admin.site.register(Parto)
admin.site.register(PartoComplicacion)
admin.site.register(PartoAnestesia)
admin.site.register(IVEAtencion)
admin.site.register(IVEAcompanamiento)
admin.site.register(AltaAnticonceptivo)