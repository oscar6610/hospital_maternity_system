"""
Utilidades para el sistema RBAC usando permisos nativos de Django.
VERSIÓN NATIVA 3.0 - Noviembre 2025

Cambios principales:
- ✅ Usa Groups y Permissions nativos de Django
- ✅ Eliminadas referencias a Rol, Permiso, RolPermiso
- ✅ Simplificado has_perm() - usa el nativo de Django
- ✅ Mantiene lógica de restricción de turno (es lógica de negocio)
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
    Permiso DRF que valida permisos usando el sistema nativo de Django.
    
    Uso en ViewSet:
        permission_classes = [IsAuthenticated, RBACPermission]
        required_permission = 'maternity.add_madrepaciente'  # Formato nativo
        
        # O con permisos dinámicos:
        def get_required_permission(self):
            if self.action == 'create':
                return 'maternity.add_madrepaciente'
            elif self.action in ['update', 'partial_update']:
                return 'maternity.change_madrepaciente'
            return 'maternity.view_madrepaciente'
        
        def check_permissions(self, request):
            self.required_permission = self.get_required_permission()
            super().check_permissions(request)
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
            logger.error(
                f"🚨 SEGURIDAD: ViewSet {view.__class__.__name__} no tiene required_permission definido"
            )
            return False
        
        # Usar has_perm() nativo de Django
        has_perm = request.user.has_perm(required_permission)
        
        if not has_perm:
            # Log de advertencia
            grupos = ', '.join([g.name for g in request.user.groups.all()]) or 'sin grupos'
            logger.warning(
                f"❌ ACCESO DENEGADO: Usuario {request.user.run} ({grupos}) "
                f"intentó acceder a {view.__class__.__name__} - Permiso requerido: {required_permission}"
            )
            
            # Registrar en auditoría
            try:
                registrar_auditoria(
                    usuario=request.user,
                    tipo_accion='PERMISSION_DENIED',
                    tabla_afectada=view.__class__.__name__,
                    id_registro=None,
                    descripcion=f'Permiso requerido: {required_permission} | Grupos: {grupos}',
                    ip_address=obtener_ip_cliente(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    resultado='FAILED'
                )
            except Exception as e:
                logger.error(f"Error al registrar auditoría de denegación: {e}")
        
        return has_perm


class RBACObjectPermission(BasePermission):
    """
    Permiso DRF para validar permisos a nivel de objeto.
    Útil para restricciones de turno en Matronas.
    
    Uso en ViewSet:
        permission_classes = [IsAuthenticated, RBACObjectPermission]
        
        def validar_permiso_objeto(self, usuario, obj):
            # Tu lógica personalizada
            return puede_modificar_registro_turno(usuario, obj)
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


def requiere_permiso(permission_codename):
    """
    Decorador para funciones que requieren un permiso nativo específico.
    
    Uso:
        @requiere_permiso('maternity.add_madrepaciente')
        def mi_vista(request):
            ...
    
    Args:
        permission_codename: Código de permiso en formato 'app_label.codename'
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.has_perm(permission_codename):
                registrar_auditoria(
                    usuario=request.user,
                    tipo_accion='PERMISSION_DENIED',
                    tabla_afectada='N/A',
                    id_registro=0,
                    descripcion=f'Acceso denegado a permiso: {permission_codename}',
                    ip_address=obtener_ip_cliente(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    resultado='FAILED'
                )
                raise PermissionDenied(f'No tiene permiso para: {permission_codename}')
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
    """
    Obtiene la dirección IP del cliente desde la request.
    
    Args:
        request: Objeto HttpRequest de Django
    
    Returns:
        str: Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def usuario_es_matrona(usuario):
    """
    Verifica si un usuario pertenece al grupo Matrona Clínica.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        bool: True si pertenece al grupo, False caso contrario
    """
    return usuario.groups.filter(name='Matrona Clínica').exists()


def usuario_es_supervisor(usuario):
    """
    Verifica si un usuario es Supervisor/Jefe de Área.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        bool: True si es supervisor, False caso contrario
    """
    return usuario.groups.filter(name='Supervisor/Jefe de Área').exists()


def usuario_es_medico(usuario):
    """
    Verifica si un usuario es Médico.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        bool: True si es médico, False caso contrario
    """
    return usuario.groups.filter(name='Médico(a)').exists()


def usuario_es_enfermero(usuario):
    """
    Verifica si un usuario es Enfermero.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        bool: True si es enfermero, False caso contrario
    """
    return usuario.groups.filter(name='Enfermero(a)').exists()


def usuario_es_administrativo(usuario):
    """
    Verifica si un usuario es Administrativo.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        bool: True si es administrativo, False caso contrario
    """
    return usuario.groups.filter(name='Administrativo(a)').exists()


def puede_modificar_registro_turno(usuario, registro):
    """
    Verifica si una Matrona puede modificar un registro específico.
    La Matrona solo puede modificar registros de su turno.
    
    NOTA: Esta es lógica de negocio, NO es parte del sistema de permisos.
    Las restricciones de turno se validan aquí independientemente de los permisos.
    
    Args:
        usuario: Instancia de Usuario (Matrona)
        registro: Objeto del registro (ej: Parto instance)
    
    Returns:
        bool: True si puede modificar, False caso contrario
    """
    # Los superusers y supervisores pueden modificar cualquier cosa
    if usuario.is_superuser or usuario_es_supervisor(usuario):
        return True
    
    # Si no es Matrona, usar permisos estándar (no aplicar restricción de turno)
    if not usuario_es_matrona(usuario):
        return True
    
    # Verificar si la Matrona tiene una restricción de turno vigente
    try:
        from core.models import RestriccionTurno
        
        restriccion = RestriccionTurno.objects.filter(
            fk_matrona=usuario,
            activo=True
        ).first()
        
        if not restriccion or not restriccion.es_vigente:
            # Sin restricción vigente, puede modificar
            return True
        
        # Verificar si el registro fue creado por la matrona
        # o si fue creado en su turno
        if hasattr(registro, 'fk_usuario_registro'):
            return registro.fk_usuario_registro == usuario
        elif hasattr(registro, 'fk_usuario_creacion'):
            return registro.fk_usuario_creacion == usuario
        elif hasattr(registro, 'fk_profesional_responsable'):
            return registro.fk_profesional_responsable == usuario
        
        # Fallback: revisar fecha_registro y verificar turno
        elif hasattr(registro, 'fecha_registro'):
            from django.utils import timezone
            fecha_registro = registro.fecha_registro
            
            # Asegurar que la fecha tenga zona horaria
            if not hasattr(fecha_registro, 'tzinfo') or fecha_registro.tzinfo is None:
                fecha_registro = timezone.make_aware(fecha_registro)
            
            turno_inicio, turno_fin = obtener_horario_turno(restriccion.turno)
            fecha_hoy = timezone.now().date()
            
            # Verificar si el registro fue creado hoy en el turno de la matrona
            if fecha_registro.date() == fecha_hoy:
                hora_registro = fecha_registro.time()
                return turno_inicio <= hora_registro < turno_fin
        
        # Si no se puede determinar, denegar por seguridad
        logger.warning(
            f"No se pudo determinar turno para registro {registro.__class__.__name__} "
            f"de matrona {usuario.run}"
        )
        return False
        
    except Exception as e:
        logger.error(f"Error verificando restricción de turno: {e}")
        # En caso de error, denegar por seguridad
        return False


def obtener_horario_turno(turno):
    """
    Obtiene el rango horario para un turno específico.
    
    Args:
        turno: Código del turno ('MATUTINO', 'VESPERTINO', 'NOCTURNO')
    
    Returns:
        tuple: (hora_inicio, hora_fin) como objetos time
    """
    from datetime import time
    
    horarios = {
        'MATUTINO': (time(8, 0), time(16, 0)),
        'VESPERTINO': (time(16, 0), time(0, 0)),
        'NOCTURNO': (time(0, 0), time(8, 0)),
    }
    
    return horarios.get(turno, (time(0, 0), time(23, 59)))


def listar_permisos_usuario(usuario):
    """
    Lista todos los permisos que tiene un usuario (directos + por grupos).
    Útil para debugging.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        dict: Diccionario con permisos directos y permisos por grupos
    """
    permisos_directos = usuario.user_permissions.values_list('codename', flat=True)
    
    permisos_por_grupos = {}
    for grupo in usuario.groups.all():
        permisos_por_grupos[grupo.name] = list(
            grupo.permissions.values_list('codename', flat=True)
        )
    
    return {
        'permisos_directos': list(permisos_directos),
        'permisos_por_grupos': permisos_por_grupos,
        'total_permisos': usuario.get_all_permissions(),
    }


def usuario_tiene_cualquier_permiso(usuario, permisos):
    """
    Verifica si un usuario tiene AL MENOS UNO de los permisos especificados.
    
    Args:
        usuario: Instancia de Usuario
        permisos: Lista de códigos de permiso ['app.perm1', 'app.perm2']
    
    Returns:
        bool: True si tiene al menos uno, False caso contrario
    """
    for permiso in permisos:
        if usuario.has_perm(permiso):
            return True
    return False


def usuario_tiene_todos_permisos(usuario, permisos):
    """
    Verifica si un usuario tiene TODOS los permisos especificados.
    
    Args:
        usuario: Instancia de Usuario
        permisos: Lista de códigos de permiso ['app.perm1', 'app.perm2']
    
    Returns:
        bool: True si tiene todos, False caso contrario
    """
    for permiso in permisos:
        if not usuario.has_perm(permiso):
            return False
    return True


def obtener_grupos_usuario(usuario):
    """
    Obtiene los nombres de todos los grupos a los que pertenece un usuario.
    
    Args:
        usuario: Instancia de Usuario
    
    Returns:
        list: Lista de nombres de grupos
    """
    return list(usuario.groups.values_list('name', flat=True))


def agregar_usuario_a_grupo(usuario, nombre_grupo):
    """
    Agrega un usuario a un grupo específico.
    
    Args:
        usuario: Instancia de Usuario
        nombre_grupo: Nombre del grupo (ej: 'Matrona Clínica')
    
    Returns:
        bool: True si se agregó exitosamente, False caso contrario
    """
    try:
        from django.contrib.auth.models import Group
        grupo = Group.objects.get(name=nombre_grupo)
        usuario.groups.add(grupo)
        logger.info(f"Usuario {usuario.run} agregado al grupo {nombre_grupo}")
        return True
    except Group.DoesNotExist:
        logger.error(f"Grupo {nombre_grupo} no existe")
        return False
    except Exception as e:
        logger.error(f"Error agregando usuario a grupo: {e}")
        return False


def remover_usuario_de_grupo(usuario, nombre_grupo):
    """
    Remueve un usuario de un grupo específico.
    
    Args:
        usuario: Instancia de Usuario
        nombre_grupo: Nombre del grupo
    
    Returns:
        bool: True si se removió exitosamente, False caso contrario
    """
    try:
        from django.contrib.auth.models import Group
        grupo = Group.objects.get(name=nombre_grupo)
        usuario.groups.remove(grupo)
        logger.info(f"Usuario {usuario.run} removido del grupo {nombre_grupo}")
        return True
    except Group.DoesNotExist:
        logger.error(f"Grupo {nombre_grupo} no existe")
        return False
    except Exception as e:
        logger.error(f"Error removiendo usuario de grupo: {e}")
        return False


def cambiar_grupo_usuario(usuario, nombre_grupo_nuevo):
    """
    Remueve al usuario de todos sus grupos actuales y lo asigna a uno nuevo.
    Útil para "cambiar de rol".
    
    Args:
        usuario: Instancia de Usuario
        nombre_grupo_nuevo: Nombre del nuevo grupo
    
    Returns:
        bool: True si se cambió exitosamente, False caso contrario
    """
    try:
        from django.contrib.auth.models import Group
        
        # Remover de todos los grupos actuales
        usuario.groups.clear()
        
        # Agregar al nuevo grupo
        grupo = Group.objects.get(name=nombre_grupo_nuevo)
        usuario.groups.add(grupo)
        
        logger.info(f"Usuario {usuario.run} cambiado al grupo {nombre_grupo_nuevo}")
        return True
    except Group.DoesNotExist:
        logger.error(f"Grupo {nombre_grupo_nuevo} no existe")
        return False
    except Exception as e:
        logger.error(f"Error cambiando grupo de usuario: {e}")
        return False