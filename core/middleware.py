"""
Middleware para registrar auditoría automáticamente en cada request.
"""
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from core.rbac_utils import registrar_auditoria, obtener_ip_cliente

logger = logging.getLogger(__name__)


class AuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware que registra todas las acciones HTTP importantes para auditoría.
    Especialmente útil para:
    - LOGIN/LOGOUT
    - Cambios de datos (POST, PUT, PATCH, DELETE)
    - Accesos denegados (403)
    """
    
    # Rutas que no se auditan (para reducir ruido)
    RUTAS_IGNORADAS = [
        '/static/',
        '/media/',
        '/health/',
        '/api/token/verify/',
        '/api/token/refresh/',
    ]
    
    def process_request(self, request):
        """Procesa la request antes de llegar a la vista."""
        request._auditoria_inicio = None
        
        # Registrar login
        if request.path == '/api/token/' and request.method == 'POST':
            # Se registrará en process_response cuando sea exitoso
            pass
        
        return None
    
    def process_response(self, request, response):
        """Procesa la response después de procesar la vista."""
        # Ignorar ciertas rutas
        if any(request.path.startswith(ruta) for ruta in self.RUTAS_IGNORADAS):
            return response
        
        # Solo registrar métodos significativos
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE', 'GET']:
            return response
        
        # Registrar intentos fallidos de acceso (403)
        if response.status_code == 403:
            self._registrar_acceso_denegado(request, response)
        
        # Registrar cambios de datos exitosos
        elif request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and response.status_code in [200, 201, 204]:
            self._registrar_cambio_exitoso(request, response)
        
        # Registrar login exitoso
        elif request.path == '/api/token/' and request.method == 'POST' and response.status_code == 200:
            self._registrar_login_exitoso(request, response)
        
        # Registrar logout exitoso
        elif request.path == '/api/logout/' and request.method == 'POST' and response.status_code == 200:
            self._registrar_logout_exitoso(request)
        
        return response
    
    def _registrar_acceso_denegado(self, request, response):
        """Registra un intento de acceso denegado."""
        try:
            registrar_auditoria(
                usuario=request.user if request.user.is_authenticated else None,
                tipo_accion='PERMISSION_DENIED',
                tabla_afectada=request.path,
                id_registro=0,
                descripcion=f'{request.method} {request.path} - Acceso denegado',
                ip_address=obtener_ip_cliente(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado='FAILED'
            )
        except Exception as e:
            logger.error(f"Error registrando acceso denegado: {e}")
    
    def _registrar_cambio_exitoso(self, request, response):
        """Registra un cambio de datos exitoso."""
        try:
            # Determinar tipo de acción
            tipo_accion_map = {
                'POST': 'CREATE',
                'PUT': 'UPDATE',
                'PATCH': 'UPDATE',
                'DELETE': 'DELETE',
            }
            tipo_accion = tipo_accion_map.get(request.method, 'UPDATE')
            
            # Intentar obtener datos de la request
            cambios_nuevos = self._obtener_datos_request(request)
            
            # Extraer tabla y ID de la URL
            tabla_afectada = request.path.split('/')[1]  # Primer componente
            id_registro = 0
            
            # Intentar extraer ID de la respuesta
            try:
                if response.status_code in [200, 201]:
                    contenido = json.loads(response.content)
                    if isinstance(contenido, dict) and 'id' in contenido:
                        id_registro = contenido['id']
                    elif isinstance(contenido, dict):
                        # Buscar campos de ID comunes
                        for campo in ['id_', 'pk', 'id_madre', 'id_parto', 'id_usuario']:
                            if campo in contenido:
                                id_registro = contenido[campo]
                                break
            except (json.JSONDecodeError, ValueError):
                pass
            
            registrar_auditoria(
                usuario=request.user if request.user.is_authenticated else None,
                tipo_accion=tipo_accion,
                tabla_afectada=tabla_afectada,
                id_registro=id_registro,
                cambios_nuevos=cambios_nuevos,
                ip_address=obtener_ip_cliente(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado='SUCCESS',
                descripcion=f'{request.method} {request.path}'
            )
        except Exception as e:
            logger.error(f"Error registrando cambio exitoso: {e}")
    
    def _registrar_login_exitoso(self, request, response):
        """Registra un login exitoso."""
        try:
            datos = self._obtener_datos_request(request)
            descripcion = f'Login exitoso - Run: {datos.get("run", "N/A")}'
            
            # El usuario aún no está autenticado en este punto, usar None o extraer del token
            registrar_auditoria(
                usuario=None,  # Se podría mejorar buscando por run
                tipo_accion='LOGIN',
                tabla_afectada='usuario',
                id_registro=0,
                ip_address=obtener_ip_cliente(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado='SUCCESS',
                descripcion=descripcion
            )
        except Exception as e:
            logger.error(f"Error registrando login: {e}")
    
    def _registrar_logout_exitoso(self, request):
        """Registra un logout exitoso."""
        try:
            registrar_auditoria(
                usuario=request.user if request.user.is_authenticated else None,
                tipo_accion='LOGOUT',
                tabla_afectada='usuario',
                id_registro=0,
                ip_address=obtener_ip_cliente(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                resultado='SUCCESS',
                descripcion='Logout exitoso'
            )
        except Exception as e:
            logger.error(f"Error registrando logout: {e}")
    
    def _obtener_datos_request(self, request):
        """Extrae datos JSON del body de la request."""
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type and 'application/json' in request.content_type:
                    return json.loads(request.body)
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass
        return {}
