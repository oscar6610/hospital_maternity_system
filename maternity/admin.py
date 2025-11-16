from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MadrePaciente, Embarazo, Parto, PartoComplicacion,
    PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo
)


@admin.register(MadrePaciente)
class MadrePacienteAdmin(admin.ModelAdmin):
    """Admin personalizado para MadrePaciente."""
    list_display = ('run', 'nombre_completo_display', 'edad_display', 'nacionalidad', 'fecha_registro')
    search_fields = ('run', 'nombre', 'apellido_paterno', 'apellido_materno')
    list_filter = ('fk_nacionalidad', 'fk_pueblo_originario', 'fecha_registro')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')
    fieldsets = (
        ('Datos Personales', {
            'fields': ('run', 'nombre', 'apellido_paterno', 'apellido_materno', 'fecha_nacimiento')
        }),
        ('Información Demográfica', {
            'fields': ('fk_nacionalidad', 'fk_pueblo_originario')
        }),
        ('Registro', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_completo_display(self, obj):
        return obj.nombre_completo()
    nombre_completo_display.short_description = 'Nombre Completo'
    
    def edad_display(self, obj):
        from datetime import date
        today = date.today()
        edad = today.year - obj.fecha_nacimiento.year - (
            (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
        )
        return f"{edad} años"
    edad_display.short_description = 'Edad'
    
    def nacionalidad(self, obj):
        return obj.fk_nacionalidad.nombre if obj.fk_nacionalidad else '-'
    nacionalidad.short_description = 'Nacionalidad'


@admin.register(Embarazo)
class EmbarazoAdmin(admin.ModelAdmin):
    """Admin personalizado para Embarazo."""
    list_display = ('id_embarazo', 'madre_nombre', 'semana_obstetrica', 'trimestre_display', 'viable_display', 'fecha_registro')
    search_fields = ('fk_madre__run', 'fk_madre__nombre')
    list_filter = ('fecha_registro',)
    readonly_fields = ('fecha_registro', 'fecha_actualizacion', 'obtener_trimestre', 'es_embarazo_viables')
    fieldsets = (
        ('Información del Embarazo', {
            'fields': ('fk_madre', 'fecha_ultima_menstruacion', 'semana_obstetrica', 'paridad', 'obtener_trimestre', 'es_embarazo_viables')
        }),
        ('Registro', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def madre_nombre(self, obj):
        return obj.fk_madre.nombre_completo()
    madre_nombre.short_description = 'Madre'
    
    def trimestre_display(self, obj):
        trimestre = obj.obtener_trimestre()
        colores = {1: '#90EE90', 2: '#FFD700', 3: '#FF6347'}
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px; color: black;">T{}</span>',
            colores.get(trimestre, '#999'),
            trimestre
        )
    trimestre_display.short_description = 'Trimestre'
    
    def viable_display(self, obj):
        viable = obj.es_embarazo_viables()
        color = '#90EE90' if viable else '#FFB6C1'
        texto = '✓ Viable' if viable else '✗ No Viable'
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, texto
        )
    viable_display.short_description = 'Viabilidad'


class PartoComplicacionInline(admin.TabularInline):
    """Inline para complicaciones de parto."""
    model = PartoComplicacion
    extra = 1
    readonly_fields = ('fecha_registro',)


class PartoAnestesiaInline(admin.TabularInline):
    """Inline para anestesias de parto."""
    model = PartoAnestesia
    extra = 1
    readonly_fields = ('fecha_registro',)


@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    """Admin personalizado para Parto."""
    list_display = ('id_parto', 'madre_nombre', 'tipo_parto', 'complicaciones_display', 'horas_trabajo_parto', 'fecha_parto')
    search_fields = ('fk_madre__run', 'fk_madre__nombre')
    list_filter = ('fk_tipo_parto', 'fecha_parto', 'fecha_registro')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion', 'tuvo_complicaciones')
    inlines = [PartoComplicacionInline, PartoAnestesiaInline]
    fieldsets = (
        ('Información del Parto', {
            'fields': ('fk_madre', 'fk_tipo_parto', 'fk_clasificacion_robson', 'fecha_parto')
        }),
        ('Profesional', {
            'fields': ('fk_profesional_responsable',)
        }),
        ('Duración y Complicaciones', {
            'fields': ('horas_trabajo_parto', 'tuvo_complicaciones')
        }),
        ('Registro', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def madre_nombre(self, obj):
        return obj.fk_madre.nombre_completo()
    madre_nombre.short_description = 'Madre'
    
    def tipo_parto(self, obj):
        return obj.fk_tipo_parto.nombre if obj.fk_tipo_parto else '-'
    tipo_parto.short_description = 'Tipo de Parto'
    
    def complicaciones_display(self, obj):
        count = obj.complicaciones.count()
        if count == 0:
            return format_html('<span style="color: green;">✓ Sin complicaciones</span>')
        return format_html(
            '<span style="color: red; font-weight: bold;">⚠ {} complicación(es)</span>',
            count
        )
    complicaciones_display.short_description = 'Estado'


@admin.register(IVEAtencion)
class IVEAtencionAdmin(admin.ModelAdmin):
    """Admin personalizado para IVEAtencion."""
    list_display = ('id_ive_atencion', 'madre_nombre', 'causal_display', 'edad_gestacional_semanas', 'fecha_atencion')
    search_fields = ('fk_madre__run', 'fk_madre__nombre')
    list_filter = ('fk_causal', 'fecha_atencion')
    readonly_fields = ('fecha_atencion',)
    fieldsets = (
        ('Información de IVE', {
            'fields': ('fk_madre', 'fk_causal', 'edad_gestacional_semanas')
        }),
        ('Registro', {
            'fields': ('fecha_atencion',),
            'classes': ('collapse',)
        }),
    )
    
    def madre_nombre(self, obj):
        return obj.fk_madre.nombre_completo()
    madre_nombre.short_description = 'Madre'
    
    def causal_display(self, obj):
        causales = {'1': 'Violación/Incesto', '2': 'Peligro vida/salud', '3': 'Inviabilidad fetal'}
        color_map = {'1': '#FFB6C1', '2': '#FFD700', '3': '#FF6347'}
        return format_html(
            '<span style="background-color: {}; padding: 3px 6px; border-radius: 3px;">{}</span>',
            color_map.get(obj.fk_causal, '#999'),
            causales.get(obj.fk_causal, obj.fk_causal)
        )
    causal_display.short_description = 'Causal'


@admin.register(IVEAcompanamiento)
class IVEAcompanamientoAdmin(admin.ModelAdmin):
    """Admin personalizado para IVEAcompanamiento."""
    list_display = ('id_acomp_ive', 'ive_id', 'tipo_profesional', 'fecha_atencion')
    search_fields = ('fk_ive_atencion__fk_madre__run', 'fk_ive_atencion__fk_madre__nombre')
    list_filter = ('tipo_profesional', 'fecha_atencion')
    readonly_fields = ('fecha_atencion',)
    
    def ive_id(self, obj):
        return f"IVE {obj.fk_ive_atencion.id_ive_atencion}"
    ive_id.short_description = 'Atención IVE'


@admin.register(AltaAnticonceptivo)
class AltaAnticonceptivoAdmin(admin.ModelAdmin):
    """Admin personalizado para AltaAnticonceptivo."""
    list_display = ('id_alta_ac', 'fk_evento', 'tipo_alta', 'metodo_display', 'esterilizacion_display', 'fecha_registro')
    search_fields = ('fk_evento',)
    list_filter = ('tipo_alta', 'esterilizacion_quirurgica', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    fieldsets = (
        ('Información del Alta', {
            'fields': ('fk_evento', 'tipo_alta')
        }),
        ('Método Anticonceptivo', {
            'fields': ('fk_metodo_anticonceptivo', 'esterilizacion_quirurgica')
        }),
        ('Registro', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )
    
    def metodo_display(self, obj):
        if not obj.fk_metodo_anticonceptivo:
            return '-'
        metodos = {'1': 'DIU', '2': 'Implante', '3': 'Esterilización', '4': 'Hormonales', '5': 'Otro'}
        return metodos.get(obj.fk_metodo_anticonceptivo, obj.fk_metodo_anticonceptivo)
    metodo_display.short_description = 'Método'
    
    def esterilizacion_display(self, obj):
        if obj.esterilizacion_quirurgica:
            return format_html('<span style="color: red; font-weight: bold;">✓ Sí</span>')
        return format_html('<span style="color: green;">✗ No</span>')
    esterilizacion_display.short_description = 'Esterilización'


@admin.register(PartoComplicacion)
class PartoComplicacionAdmin(admin.ModelAdmin):
    """Admin personalizado para PartoComplicacion."""
    list_display = ('id_complicacion', 'parto_id', 'complicacion_nombre', 'histerectomia_obstetrica', 'transfusion_sanguinea', 'fecha_registro')
    search_fields = ('fk_parto__fk_madre__run', 'fk_complicacion__nombre')
    list_filter = ('histerectomia_obstetrica', 'transfusion_sanguinea', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    
    def parto_id(self, obj):
        return obj.fk_parto.id_parto
    parto_id.short_description = 'Parto'
    
    def complicacion_nombre(self, obj):
        return obj.fk_complicacion.nombre
    complicacion_nombre.short_description = 'Complicación'


@admin.register(PartoAnestesia)
class PartoAnestesiaAdmin(admin.ModelAdmin):
    """Admin personalizado para PartoAnestesia."""
    list_display = ('id_anestesia', 'parto_id', 'tipo_anestesia', 'solicitada_por_paciente', 'fecha_registro')
    search_fields = ('fk_parto__fk_madre__run', 'tipo_anestesia')
    list_filter = ('tipo_anestesia', 'solicitada_por_paciente', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    
    def parto_id(self, obj):
        return obj.fk_parto.id_parto
    parto_id.short_description = 'Parto'