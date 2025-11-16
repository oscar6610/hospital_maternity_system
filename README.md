# Sistema Hospitalario de Maternidad y Neonatología

Sistema de gestión hospitalaria para el registro y seguimiento de partos, recién nacidos y generación de reportes REM (Reporte Estadístico Mensual).

## Estructura del Proyecto

El proyecto está organizado en los siguientes módulos:

### Módulos de la Aplicación

- **core**: Gestión de usuarios basada en `AbstractUser`, autenticación JWT, roles y permisos (RBAC)
- **catalogs**: Catálogos de datos estáticos (nacionalidades, pueblos originarios, tipos de parto, etc.)
- **maternity**: Gestión de madres pacientes, embarazos, partos e IVE
- **neonatology**: Gestión de recién nacidos, tamizajes y egresos
- **compliance**: Auditoría y trazabilidad de movimientos
- **alerts**: Sistema de alertas automáticas
- **reports**: Generación de reportes REM
- **api**: Endpoints REST, viewsets y routers centralizados

## Tecnologías

- Python 3.11+
- Django 5.2.8
- Django REST Framework 3.16.1
- SimpleJWT 5.5.1 (autenticación por tokens JWT)
- MySQL 8.0+ (configurable a PostgreSQL)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repositorio>
cd hospital_maternity_system
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
DB_ENGINE=django.db.backends.mysql
DB_NAME=hospital_maternity_system
DB_USER=root
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=3306
CORS_ALLOW_ALL_ORIGINS=False
```

### 5. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

Ingresa:

- RUN: Tu RUT (ej: 12345678-9)
- Email: Tu email
- Password: Tu contraseña segura

### 7. Ejecutar servidor

```bash
python manage.py runserver
```

---

## Autenticación JWT

El sistema utiliza **JWT (JSON Web Tokens)** para autenticación sin estado en la API REST.

### Flujo de autenticación

1. **Login**: Envía credenciales (run + password)

   ```bash
   POST /api/auth/token/
   ```

   Recibe: `access_token` (60 min) + `refresh_token` (7 días)

2. **Usar API**: Incluye token en header Authorization

   ```bash
   Authorization: Bearer {access_token}
   ```

3. **Refrescar token**: Cuando el access token expire
   ```bash
   POST /api/auth/token/refresh/
   ```

### Ejemplo de login con cURL

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"run": "12345678-9", "password": "tu_contraseña"}'
```

**Respuesta**:

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id_usuario": 1,
    "run": "12345678-9",
    "nombre_completo": "Juan García",
    "email": "juan@hospital.com",
    "rol_nombre": "Médico",
    "is_active": true
  }
}
```

### Ejemplo de petición autenticada

```bash
curl -H "Authorization: Bearer {access_token}" \
  http://localhost:8000/api/usuarios/me/
```

---

## Endpoints API

Base URL: `http://127.0.0.1:8000/api/`

### 🔐 Autenticación (JWT)

```
POST   /auth/token/               - Login (obtener tokens)
POST   /auth/token/refresh/       - Refrescar access token
```

### 👤 Usuarios

```
GET    /usuarios/                 - Listar usuarios
POST   /usuarios/                 - Crear usuario
GET    /usuarios/{id}/            - Obtener usuario
PUT    /usuarios/{id}/            - Actualizar usuario
DELETE /usuarios/{id}/            - Eliminar usuario
GET    /usuarios/me/              - Perfil del usuario autenticado
POST   /usuarios/{id}/change_password/  - Cambiar contraseña
POST   /usuarios/{id}/logout/     - Logout
```

### 🎛️ Administración

```
GET    /roles/                    - Listar roles
POST   /roles/                    - Crear rol
GET    /permisos/                 - Listar permisos
POST   /permisos/                 - Crear permiso
GET    /roles-permisos/           - Asociaciones rol-permiso
```

### 📚 Catálogos

```
GET    /catalogs/nacionalidades/
GET    /catalogs/pueblos-originarios/
GET    /catalogs/complicaciones-parto/
GET    /catalogs/robson/
GET    /catalogs/tipos-parto/
```

### 👶 Maternidad

```
GET    /maternity/madres/
GET    /maternity/embarazos/
GET    /maternity/partos/
GET    /maternity/partos-complicaciones/
GET    /maternity/partos-anestesias/
GET    /maternity/ive-atenciones/
GET    /maternity/ive-acompanamientos/
GET    /maternity/altas-anticonceptivos/
```

### 👶 Neonatología

```
GET    /neonatology/recien-nacidos/
GET    /neonatology/atenciones-inmediatas/
GET    /neonatology/tamizajes-metabolicos/
GET    /neonatology/tamizajes-auditivos/
GET    /neonatology/tamizajes-cardiopatias/
GET    /neonatology/egresos/
```

### 📋 Cumplimiento

```
GET    /compliance/trazas/        - Auditoría (solo lectura)
```

### ⚠️ Alertas

```
GET    /alerts/alertas/           - Alertas del sistema
```

### 📊 Reportes

```
GET    /reports/reportes-rem/
GET    /reports/reportes-rem-detalles/
```

---

## Estructura de URLs

```
config/urls.py
├── /admin/                      - Django admin
├── /api/
│   ├── /auth/token/             - Login JWT
│   ├── /auth/token/refresh/     - Refrescar token
│   ├── /usuarios/               - Gestión de usuarios
│   ├── /roles/                  - Gestión de roles
│   ├── /permisos/               - Gestión de permisos
│   ├── /catalogs/*              - Catálogos
│   ├── /maternity/*             - Maternidad
│   ├── /neonatology/*           - Neonatología
│   ├── /compliance/*            - Cumplimiento
│   ├── /alerts/*                - Alertas
│   └── /reports/*               - Reportes
└── /api-auth/                   - Autenticación de sesión (legacy)
```

**Nota**: Todos los viewsets están centralizados en `api/routers.py` para mantener el código ordenado y escalable.

---

## Administración

### Panel Admin

Disponible en: `http://127.0.0.1:8000/admin/`

**Credenciales**: Usuario superusuario creado en instalación

**Funcionalidades**:

- Gestión de usuarios (crear, editar, eliminar)
- Cambio de contraseñas
- Gestión de roles y permisos
- Auditoría y logs

---

## Configuración

### Archivos principales de configuración

- `config/settings.py` - Configuraciones de Django

  - `AUTH_USER_MODEL = 'core.Usuario'` - Modelo de usuario personalizado
  - `SIMPLE_JWT` - Configuración de tokens JWT
  - `REST_FRAMEWORK` - Configuración de autenticación y permisos

- `.env` - Variables de entorno

### Tokens JWT

**Tiempos de expiración** (configurables en `settings.py`):

- **Access Token**: 60 minutos
- **Refresh Token**: 7 días

**Características**:

- Rotación automática de refresh tokens
- Blacklist después de rotación
- Algoritmo: HS256

---

## Testing

### Ejecutar tests

```bash
python manage.py test core -v 2          # Tests de core (autenticación)
python manage.py test                    # Todos los tests
```

### Tests incluidos

- `core.tests.UsuarioModelTest` (6 tests) - Modelo de usuario
- `core.tests.UsuarioAuthenticationAPITest` (5 tests) - Autenticación JWT
- `core.tests.ChangePasswordAPITest` (4 tests) - Cambio de contraseña
- `core.tests.RolPermisoTest` (4 tests) - Roles y permisos

---

## Documentación adicional

- `JWT_AUTH_README.md` - Guía completa de autenticación JWT
- Consultar docstrings en modelos y viewsets para más detalles

---

## Seguridad

### Recomendaciones para producción

1. **Configurar DEBUG=False**
2. **Usar HTTPS** (SECURE_SSL_REDIRECT=True)
3. **Configurar CORS** con orígenes específicos
4. **Variables de entorno** para SECRET_KEY y credenciales
5. **ALLOWED_HOSTS** específicos
6. **Token blacklist** para logout verdadero (opcional)

### Variables de seguridad en `settings.py`

```python
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## Contribución

1. Crear rama desde `main`
2. Realizar cambios
3. Hacer commit con mensajes descriptivos
4. Crear Pull Request

---

## Licencia

Proyecto privado - Todos los derechos reservados

---

## Soporte

Para reportar problemas o sugerencias, contactar al equipo de desarrollo.
