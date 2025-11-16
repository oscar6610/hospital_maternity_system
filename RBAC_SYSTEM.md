# Sistema RBAC (Role-Based Access Control)

## Descripción General

El sistema RBAC implementado en este proyecto proporciona un control de acceso granular basado en roles y permisos específicos. Todos los usuarios tienen un rol asignado, y cada rol tiene un conjunto específico de permisos.

## Estructura del Sistema

### Modelos Principales

1. **Rol** (`core.models.Rol`)

   - Almacena los roles disponibles del sistema
   - Roles predefinidos: Matrona Clínica, Supervisor/Jefe, Médico, Enfermero, Administrativo
   - Cada rol tiene una relación de muchos a muchos con Permisos

2. **Permiso** (`core.models.Permiso`)

   - Almacena los permisos granulares del sistema
   - Códigos de permiso: `categoria:recurso:accion` (ej: `maternity:mother:create`)
   - Incluye categorías: catalog, maternity, neonatology, reports, alerts, compliance, core
   - Cada permiso tiene una descripción detallada

3. **RolPermiso** (`core.models.RolPermiso`)

   - Tabla de asociación entre Roles y Permisos
   - Permite asignar múltiples permisos a un rol

4. **TrazaMovimiento** (`core.models.TrazaMovimiento`)

   - Registro de auditoría de todas las acciones importantes
   - Almacena: usuario, tipo de acción, tabla afectada, cambios antes/después, IP, resultado
   - Campos de índice para búsquedas rápidas

5. **RestriccionTurno** (`core.models.RestriccionTurno`)
   - Restricción específica para Matronas
   - Define el turno de trabajo y las fechas de validez
   - Limita el acceso de la Matrona a registros de su turno

## Roles y Permisos

### 1. Matrona Clínica

**Descripción**: Responsable de registrar datos del parto y recién nacido.
**Restricción crítica**: Solo puede modificar registros de su turno.

**Permisos**:

- `catalog:read` - Consultar catálogos
- `maternity:mother:create` - Registrar madres
- `maternity:mother:read` - Consultar madres
- `maternity:mother:update` - Actualizar madres
- `maternity:delivery:create` - Registrar partos
- `maternity:delivery:read` - Consultar partos
- `maternity:delivery:update_own` - Actualizar partos propios
- `maternity:ive:manage` - Gestionar IVE
- `maternity:complication:manage` - Gestionar complicaciones
- `maternity:contraceptive:manage` - Gestionar anticoncepción
- `neonatal:rn:create` - Registrar RN
- `neonatal:rn:read` - Consultar RN
- `neonatal:rn:update_immediate` - Registrar datos inmediatos
- `neonatal:tamizaje:manage` - Gestionar tamizajes
- `neonatal:discharge:manage` - Gestionar alta
- `alert:read` - Visualizar alertas

### 2. Supervisor/Jefe de Área

**Descripción**: Acceso completo, reportes, y gestión de usuarios.

**Permisos**: Todos excepto algunos específicos de ejecución médica.

### 3. Médico(a)

**Descripción**: Consulta información clínica y actualiza estados de salud.

**Permisos Clave**:

- Lectura de madres y RN
- Actualización de registros de parto
- Gestión de complicaciones
- Gestión de tamizajes

### 4. Enfermero(a)

**Descripción**: Registra procedimientos y administración de medicamentos.

**Permisos Clave**:

- Lectura de madres y RN
- Actualización inmediata de RN
- Gestión de tamizajes
- Gestión de alta

### 5. Administrativo(a)

**Descripción**: Gestiona datos de ingreso y coordinación de alta.

**Permisos Clave**:

- Creación de madres
- Lectura de información general
- Gestión de alta del binomio

## Uso en ViewSets

### Proteger un ViewSet con RBAC

```python
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from core.rbac_utils import RBACPermission
from maternity.models import MadrePaciente
from maternity.serializers import MadrePacienteSerializer

class MadrePacienteViewSet(ModelViewSet):
    queryset = MadrePaciente.objects.all()
    serializer_class = MadrePacienteSerializer
    permission_classes = [IsAuthenticated, RBACPermission]

    # Especificar el permiso requerido
    required_permission = 'maternity:mother:read'
```

### Proteger Acciones Específicas

```python
class PartoViewSet(ModelViewSet):
    queryset = Parto.objects.all()
    serializer_class = PartoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]

    def get_required_permission(self):
        """Devolver diferentes permisos según la acción"""
        if self.action == 'create':
            return 'maternity:delivery:create'
        elif self.action in ['update', 'partial_update']:
            return 'maternity:delivery:update_all'
        elif self.action == 'destroy':
            return 'maternity:delivery:delete'
        return 'maternity:delivery:read'

    def check_permissions(self, request):
        """Override para usar el permiso dinámico"""
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)
```

### Proteger a Nivel de Objeto (Restricción de Turno)

```python
from core.rbac_utils import RBACObjectPermission, puede_modificar_registro_turno

class PartoViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, RBACObjectPermission]

    def validar_permiso_objeto(self, usuario, obj):
        """Validación a nivel de objeto"""
        return puede_modificar_registro_turno(usuario, obj)
```

## Funciones de Utilidad

### Verificar Permiso

```python
from core.rbac_utils import tiene_permiso

if tiene_permiso(usuario, 'maternity:mother:create'):
    # Usuario tiene permiso
    ...
```

### Decorador para Vistas Basadas en Funciones

```python
from core.rbac_utils import requiere_permiso

@requiere_permiso('maternity:mother:read')
def mi_vista(request):
    # Solo usuarios con este permiso pueden acceder
    ...
```

### Verificar Tipo de Usuario

```python
from core.rbac_utils import (
    usuario_es_matrona,
    usuario_es_supervisor,
    usuario_es_medico,
    usuario_es_enfermero,
    usuario_es_administrativo
)

if usuario_es_matrona(request.user):
    # Aplicar lógica específica de Matrona
    ...
```

### Auditoría Manual

```python
from core.rbac_utils import registrar_auditoria, obtener_ip_cliente

registrar_auditoria(
    usuario=request.user,
    tipo_accion='CREATE',
    tabla_afectada='madre_paciente',
    id_registro=madre.id_madre,
    cambios_nuevos={'nombre': madre.nombre},
    ip_address=obtener_ip_cliente(request),
    resultado='SUCCESS'
)
```

## Restricción de Turno para Matronas

### Crear una Restricción de Turno

```python
from core.models import RestriccionTurno
from datetime import date

restriccion = RestriccionTurno.objects.create(
    fk_matrona=usuario_matrona,
    turno='MATUTINO',  # MATUTINO, VESPERTINO, NOCTURNO
    fecha_inicio=date.today(),
    fecha_fin=None,  # Indefinido
    activo=True,
    observaciones='Matrona asignada al turno matutino'
)
```

### Verificar Restricción

```python
from core.rbac_utils import puede_modificar_registro_turno

# Verificar si la Matrona puede modificar un parto específico
if puede_modificar_registro_turno(matrona, parto):
    # Permitir modificación
    ...
else:
    # Denegar modificación - parto de otro turno
    ...
```

## Auditoría

### Consultar Trazas

```python
from core.models import TrazaMovimiento
from django.utils import timezone
from datetime import timedelta

# Trazas de los últimos 7 días
hace_7_dias = timezone.now() - timedelta(days=7)
trazas = TrazaMovimiento.objects.filter(
    fecha_hora__gte=hace_7_dias
).order_by('-fecha_hora')

# Filtrar por usuario
trazas_usuario = TrazaMovimiento.objects.filter(
    fk_usuario=usuario
).order_by('-fecha_hora')

# Filtrar por tipo de acción
intentos_fallidos = TrazaMovimiento.objects.filter(
    resultado='FAILED'
)
```

### Middleware de Auditoría

El middleware `core.middleware.AuditoriaMiddleware` registra automáticamente:

- Logins exitosos
- Logouts
- Cambios de datos (CREATE, UPDATE, DELETE)
- Intentos de acceso denegado
- Cambios a nivel de IP y User Agent

## Seguridad y Mejores Prácticas

1. **Siempre verificar permisos** en viewsets y vistas importantes
2. **Usar el decorador `@requiere_permiso`** en vistas basadas en funciones
3. **Registrar auditoría** de operaciones sensibles manualmente si es necesario
4. **Revisar logs de auditoría** regularmente
5. **Gestionar restricciones de turno** de Matronas en el admin
6. **Usar `IsAuthenticated`** siempre que sea posible
7. **Nunca confiar** solo en autenticación, verificar permisos

## Administración en Django Admin

### Ver Roles y Permisos

1. Ir a `http://localhost:8000/admin/`
2. Navegar a "Rol" para ver/editar roles
3. Navegar a "Permiso" para ver permisos disponibles
4. Navegar a "Rol-Permiso" para asignar permisos a roles
5. Navegar a "Restricción Turno" para gestionar turnos de Matronas
6. Navegar a "Traza de Movimiento" para consultar auditoría

### Crear Nuevo Rol

1. Admin > Core > Rol > Add Rol
2. Seleccionar nombre del rol
3. Agregar descripción
4. Guardar

### Asignar Permisos a Rol

1. Admin > Core > Rol-Permiso > Add Rol-Permiso
2. Seleccionar Rol y Permiso
3. Guardar

## Instalación de Datos Iniciales

Se puede cargar el sistema RBAC con un comando personalizado:

```bash
python manage.py load_rbac_system
```

Este comando crea:

- 24 permisos con categorización
- 5 roles predefinidos
- Asignaciones de permisos a cada rol

## Configuración

No se requiere configuración adicional en settings.py más allá de lo ya implementado:

- Middleware agregado: `core.middleware.AuditoriaMiddleware`
- Modelos registrados en admin automáticamente

## Extensibilidad

El sistema está diseñado para ser extensible:

1. **Agregar nuevos permisos**: Simplemente crear instancias de `Permiso` con nuevos códigos
2. **Crear nuevos roles**: Crear instancias de `Rol` y asignar permisos
3. **Personalizar restricciones**: Extender `RestriccionTurno` para otras restricciones horarias
4. **Auditoría personalizada**: Llamar a `registrar_auditoria()` en puntos clave

## Notas de Seguridad

- Las contraseñas nunca se registran en auditoría
- Los tokens JWT no se registran completos
- Las restricciones de turno usan la propiedad `es_vigente` para validación
- Los superusers siempre tienen acceso completo (usar con cuidado)
- El middleware filtra ciertas rutas (/static/, /media/) para reducir ruido de auditoría
