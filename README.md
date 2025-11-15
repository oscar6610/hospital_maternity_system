# Sistema Hospitalario de Maternidad y Neonatología

Sistema de gestión hospitalaria para el registro y seguimiento de partos, recién nacidos y generación de reportes REM (Reporte Estadístico Mensual).

## Estructura del Proyecto

El proyecto está organizado en los siguientes módulos:

### Módulos de la Aplicación

- **core**: Gestión de usuarios, roles y permisos (RBAC)
- **catalogs**: Catálogos de datos estáticos (nacionalidades, pueblos originarios, tipos de parto, etc.)
- **maternity**: Gestión de madres pacientes, embarazos, partos e IVE
- **neonatology**: Gestión de recién nacidos, tamizajes y egresos
- **compliance**: Auditoría y trazabilidad de movimientos
- **alerts**: Sistema de alertas automáticas
- **reports**: Generación de reportes REM
- **api**: Endpoints REST, viewsets y routers

## Tecnologías

- Python 3.x
- Django 5.x
- Django REST Framework
- SQLite (desarrollo) / PostgreSQL (producción recomendada)

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual:
```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
   pip install -r requirements.txt
```

4. Ejecutar migraciones:
```bash
   python manage.py migrate
```

5. Crear superusuario:
```bash
   python manage.py createsuperuser
```

6. Ejecutar servidor:
```bash
   python manage.py runserver
```

## Endpoints API

La API REST está disponible en: `http://127.0.0.1:8000/api/`

### Core
- `/api/usuarios/` - Gestión de usuarios
- `/api/roles/` - Gestión de roles
- `/api/permisos/` - Gestión de permisos

### Catalogs
- `/api/catalogs/nacionalidades/`
- `/api/catalogs/pueblos-originarios/`
- `/api/catalogs/complicaciones-parto/`
- `/api/catalogs/robson/`
- `/api/catalogs/tipos-parto/`

### Maternity
- `/api/maternity/madres/`
- `/api/maternity/embarazos/`
- `/api/maternity/partos/`
- `/api/maternity/partos-complicaciones/`
- `/api/maternity/partos-anestesias/`
- `/api/maternity/ive-atenciones/`
- `/api/maternity/ive-acompanamientos/`
- `/api/maternity/altas-anticonceptivos/`

### Neonatology
- `/api/neonatology/recien-nacidos/`
- `/api/neonatology/atenciones-inmediatas/`
- `/api/neonatology/tamizajes-metabolicos/`
- `/api/neonatology/tamizajes-auditivos/`
- `/api/neonatology/tamizajes-cardiopatias/`
- `/api/neonatology/egresos/`

### Compliance
- `/api/compliance/trazas/` - Trazabilidad (solo lectura)

### Alerts
- `/api/alerts/alertas/` - Alertas del sistema

### Reports
- `/api/reports/reportes-rem/`
- `/api/reports/reportes-rem-detalles/`

## Autenticación

El sistema utiliza autenticación basada en sesión de Django. Para acceder a los endpoints es necesario estar autenticado.

## Admin

Panel de administración disponible en: `http://127.0.0.1:8000/admin/`

## Configuración

Las configuraciones principales se encuentran en `config/settings.py`

## Licencia

Proyecto privado - Todos los derechos reservados