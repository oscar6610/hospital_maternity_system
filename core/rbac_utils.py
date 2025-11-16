"""
Utilidades para el sistema RBAC: decoradores, mixins y funciones de permiso.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
import logging

logger = logging.getLogger(__name__)


class RBACPermission(BasePermission):
    """
    Permiso DRF para validar permisos basados en RBAC.
    
    Uso en ViewSet:
        permission_classes = [RBACPermission]
        required_permission = 'maternity:mother:read'
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los superusers tienen acceso a todo
        if request.user.is_superuser:
            return True
        
        # Obtener el permiso requerido del viewset
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True  # Si no hay permiso requerido, permitir
        
        # Verificar si el usuario tiene el permiso
        return tiene_permiso(request.user, required_permission)


class RBACObjectPermission(BasePermission):
    """
    Permiso DRF para validar permisos a nivel de objeto.
    Útil para restricciones de turno en Matronas.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los superusers tienen acceso a todo
        if request.user.is_superuser:
            return True
        
        # Obtener la función de validación del viewset
        validador = getattr(view, 'validar_permiso_objeto', None)
        if not validador:
            return True
        
        return validador(request.user, obj)


def tiene_permiso(usuario, codigo_permiso):
    """
    Verifica si un usuario tiene un permiso específico.
    
    Args:
        usuario: Instancia de Usuario
        codigo_permiso: Código del permiso (ej: 'maternity:mother:read')
    
    Returns:
        bool: True si tiene el permiso, False caso contrario
    """
    if usuario.is_superuser:
        return True
    
    if not usuario.fk_rol:
        return False
    
    return usuario.fk_rol.permisos.filter(codigo_permiso=codigo_permiso, activo=True).exists()


def requiere_permiso(codigo_permiso):
    """
    Decorador para funciones que requieren un permiso específico.
    
    Uso:
        @requiere_permiso('maternity:mother:read')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not tiene_permiso(request.user, codigo_permiso):
                registrar_auditoria(
                    usuario=request.user,
                    tipo_accion='PERMISSION_DENIED',
                    tabla_afectada='N/A',
                    id_registro=0,
                    descripcion=f'Acceso denegado a {codigo_permiso}',
                    ip_address=obtener_ip_cliente(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    resultado='FAILED'
                )
                raise PermissionDenied(f'No tiene permiso para: {codigo_permiso}')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def registrar_auditoria(usuario, tipo_accion, tabla_afectada, id_registro, 
                        cambios_anteriores=None, cambios_nuevos=None,
                        ip_address=None, user_agent=None, resultado='SUCCESS',
                        descripcion=''):
    """
    Registra una acción en la auditoría del sistema.
    
    Args:
        usuario: Instancia de Usuario (puede ser None)
        tipo_accion: Tipo de acción (CREATE, UPDATE, DELETE, READ, LOGIN, LOGOUT, PERMISSION_DENIED)
        tabla_afectada: Nombre de la tabla/modelo
        id_registro: ID del registro afectado
        cambios_anteriores: Dict con valores anteriores
        cambios_nuevos: Dict con valores nuevos
        ip_address: Dirección IP del cliente
        user_agent: User Agent del navegador
        resultado: SUCCESS o FAILED
        descripcion: Descripción adicional
    """
    try:
        # Importar localmente para evitar ciclos de importación entre apps
        from compliance.models import TrazaMovimiento

        TrazaMovimiento.objects.create(
            fk_usuario=usuario,
            tipo_accion=tipo_accion,
            tabla_afectada=tabla_afectada,
            id_registro=id_registro,
            cambios_anteriores=cambios_anteriores,
            cambios_nuevos=cambios_nuevos,
            ip_address=ip_address,
            user_agent=user_agent,
            resultado=resultado,
            descripcion=descripcion
        )
    except Exception as e:
        logger.error(f"Error registrando auditoría: {e}")


def obtener_ip_cliente(request):
    """Obtiene la dirección IP del cliente desde la request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def usuario_es_matrona(usuario):
    """Verifica si un usuario es Matrona Clínica."""
    return usuario.fk_rol and usuario.fk_rol.nombre_rol == 'matrona_clinica'


def usuario_es_supervisor(usuario):
    """Verifica si un usuario es Supervisor/Jefe de Área."""
    return usuario.fk_rol and usuario.fk_rol.nombre_rol == 'supervisor_jefe'


def usuario_es_medico(usuario):
    """Verifica si un usuario es Médico."""
    return usuario.fk_rol and usuario.fk_rol.nombre_rol == 'medico'


def usuario_es_enfermero(usuario):
    """Verifica si un usuario es Enfermero."""
    return usuario.fk_rol and usuario.fk_rol.nombre_rol == 'enfermero'


def usuario_es_administrativo(usuario):
    """Verifica si un usuario es Administrativo."""
    return usuario.fk_rol and usuario.fk_rol.nombre_rol == 'administrativo'


def puede_modificar_registro_turno(usuario, registro):
    """
    Verifica si una Matrona puede modificar un registro específico.
    La Matrona solo puede modificar registros de su turno.
    
    Args:
        usuario: Instancia de Usuario (Matrona)
        registro: Objeto del registro (ej: Parto instance)
    
    Returns:
        bool: True si puede modificar, False caso contrario
    """
    # Los superusers y supervisores pueden modificar cualquier cosa
    if usuario.is_superuser or usuario_es_supervisor(usuario):
        return True
    
    # Si no es Matrona, usar lógica específica
    if not usuario_es_matrona(usuario):
        return False
    
    # Verificar si la Matrona tiene una restricción de turno vigente
    try:
        restriccion = usuario.restriccion_turno
        if restriccion.es_vigente:
            # La Matrona solo puede modificar registros que ella creó
            # o registros creados en su turno
            if hasattr(registro, 'fk_usuario_registro'):
                return registro.fk_usuario_registro == usuario
            # Si el registro tiene fk_usuario_creacion
            elif hasattr(registro, 'fk_usuario_creacion'):
                return registro.fk_usuario_creacion == usuario
            # Fallback: revisar fecha_creacion
            elif hasattr(registro, 'fecha_creacion'):
                from django.utils import timezone
                fecha_creacion = timezone.make_aware(
                    timezone.datetime.combine(
                        timezone.now().date(),
                        timezone.datetime.min.time()
                    )
                ) if not hasattr(registro.fecha_creacion, 'tzinfo') else registro.fecha_creacion
                
                turno_inicio, turno_fin = obtener_horario_turno(restriccion.turno)
                fecha_hoy = timezone.now().date()
                
                if fecha_creacion.date() == fecha_hoy:
                    hora_creacion = fecha_creacion.time()
                    return turno_inicio <= hora_creacion < turno_fin
    except Exception as e:
        logger.error(f"Error verificando restricción de turno: {e}")
    
    return False


def obtener_horario_turno(turno):
    """
    Obtiene el rango horario para un turno específico.
    
    Returns:
        tuple: (hora_inicio, hora_fin) como objetos time
    """
    from datetime import time
    
    horarios = {
        'MATUTINO': (time(8, 0), time(16, 0)),
        'VESPERTINO': (time(16, 0), time(0, 0)),  # Hasta medianoche, luego toca nocturno
        'NOCTURNO': (time(0, 0), time(8, 0)),
    }
    
    return horarios.get(turno, (time(0, 0), time(0, 0)))
