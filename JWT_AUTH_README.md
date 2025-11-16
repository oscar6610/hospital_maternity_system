# Sistema de Autenticación JWT - Hospital Maternity System

## Resumen de cambios implementados

Se ha reemplazado completamente el modelo de autenticación del sistema. Los cambios principales incluyen:

### 1. Modelo Usuario actualizado (AbstractUser)

- **Archivo**: `core/models.py`
- `Usuario` ahora hereda de `AbstractUser` de Django
- Usa `run` como campo de identificación única (USERNAME_FIELD)
- Implementa `UsuarioManager` personalizado para crear usuarios y superusuarios
- Campos principales:
  - `id_usuario` (PK custom)
  - `run` (único, identificador de login)
  - `email` (único)
  - `nombre_completo`
  - `fk_rol` (relación con Rol)
  - Hereda: `password`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`

### 2. Sistema de autenticación JWT (SimpleJWT)

- **Dependencia**: `djangorestframework-simplejwt==5.5.1`
- **Configuración**: `config/settings.py`
- Tokens:
  - Access Token: válido por 60 minutos
  - Refresh Token: válido por 7 días
  - Rotation automático de refresh tokens

### 3. Vistas de autenticación (core/views.py)

- `CustomTokenObtainPairView`: Endpoint de login que retorna access/refresh tokens
- `UsuarioViewSet`:
  - `GET /api/usuarios/me/` - Perfil del usuario autenticado
  - `POST /api/usuarios/{id}/change_password/` - Cambiar contraseña
  - `POST /api/usuarios/{id}/logout/` - Logout (confirmación)
  - CRUD estándar para administración de usuarios

### 4. Serializers de autenticación (core/serializers.py)

- `LoginSerializer`: Validación de credenciales (run + password)
- `ChangePasswordSerializer`: Cambio de contraseña con validaciones
- `UsuarioProfileSerializer`: Perfil público del usuario
- `UsuarioSerializer`: CRUD completo

### 5. URLs y rutas (centralizadas en api/routers.py)

Las rutas de autenticación JWT están centralizadas en `api/routers.py`:

```
POST   /api/auth/token/                     - Obtener tokens (login)
POST   /api/auth/token/refresh/             - Refrescar access token
GET    /api/usuarios/                       - Listar usuarios
POST   /api/usuarios/                       - Crear usuario
GET    /api/usuarios/{id}/                  - Obtener usuario
PUT    /api/usuarios/{id}/                  - Actualizar usuario
DELETE /api/usuarios/{id}/                  - Eliminar usuario
GET    /api/usuarios/me/                    - Perfil del usuario autenticado
POST   /api/usuarios/{id}/change_password/  - Cambiar contraseña
POST   /api/usuarios/{id}/logout/           - Logout (confirmación)
```

**Nota**: Los viewsets de `core` (Usuario, Rol, Permiso, RolPermiso) están ubicados en `api/viewsets.py`
y se registran mediante el router centralizado en `api/routers.py`.

### 6. Tests completos (core/tests.py)

- `UsuarioModelTest`: Tests del modelo Usuario
- `UsuarioAuthenticationAPITest`: Tests de autenticación JWT
- `ChangePasswordAPITest`: Tests de cambio de contraseña
- `RolPermisoTest`: Tests de roles y permisos

---

## Pasos para implementar en tu base de datos

### Paso 1: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Crear migraciones

```bash
python manage.py makemigrations core
python manage.py makemigrations
```

**⚠️ IMPORTANTE**: Este paso cambiará la estructura de la tabla `usuario`:

- Reemplaza `contrasena_hash` con `password` (estándar de Django)
- Añade campos de `AbstractUser`: `is_staff`, `is_superuser`, `is_active`, `date_joined`, `last_login`
- Mantiene: `id_usuario`, `run`, `email`, `nombre_completo`, `fk_rol`

### Paso 3: Aplicar migraciones (crea nueva tabla si es necesario)

```bash
python manage.py migrate
```

**Nota sobre datos existentes**: Si tienes usuarios en la tabla antigua:

1. Haz backup de la BD
2. Puedes crear una migración de datos personalizada para transferir contraseñas/datos
3. O ejecuta `migrate` y crea nuevamente los usuarios

### Paso 4: Crear superusuario

```bash
python manage.py createsuperuser
```

Ingresa:

- RUN: `12345678-9` (tu RUT)
- Email: `admin@hospital.com`
- Nombre completo: (opcional en createsuperuser)
- Password: Tu contraseña segura

---

## Cómo usar el sistema JWT

### 1. Obtener tokens (login)

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"run": "12345678-9", "password": "tu_contraseña"}'
```

**Respuesta exitosa**:

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id_usuario": 1,
    "run": "12345678-9",
    "nombre_completo": "Juan García",
    "email": "juan@hospital.com",
    "fk_rol": 1,
    "rol_nombre": "Médico",
    "is_active": true,
    "date_joined": "2025-11-15T10:30:00Z"
  }
}
```

### 2. Usar el access token en peticiones protegidas

Incluye el token en el header `Authorization`:

```bash
curl -H "Authorization: Bearer {access_token}" \
  http://localhost:8000/api/usuarios/me/
```

### 3. Refrescar token (sin volver a loguear)

Cuando el access token expire en 60 minutos:

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "{refresh_token}"}'
```

**Respuesta**:

```json
{
  "access": "nuevo_access_token",
  "refresh": "nuevo_refresh_token" // Si ROTATE_REFRESH_TOKENS=True
}
```

### 4. Cambiar contraseña

```bash
curl -X POST http://localhost:8000/api/usuarios/{id_usuario}/change_password/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "contraseña_actual",
    "new_password": "nueva_contraseña_segura",
    "new_password_confirm": "nueva_contraseña_segura"
  }'
```

### 5. Obtener perfil del usuario autenticado

```bash
curl -H "Authorization: Bearer {access_token}" \
  http://localhost:8000/api/usuarios/me/
```

---

## Estructura de archivos actualizada

### Arquitectura centralizada (Opción 1 - Recomendada)

```
config/
├── urls.py                    - URL principal
│   └── path('api/', include('api.urls'))    ← Todo centralizado aquí
│
api/
├── routers.py                 - Router centralizado (118+ rutas)
│   ├── JWT Auth URLs
│   │   ├── auth/token/
│   │   └── auth/token/refresh/
│   ├── ViewSets (desde api/viewsets.py)
│   │   ├── UsuarioViewSet
│   │   ├── RolViewSet
│   │   ├── PermisoViewSet
│   │   └── ... (todos los viewsets)
│   └── urlpatterns = auth_urls + router.urls
├── urls.py                    - Importa urlpatterns de routers
└── viewsets.py                - Todos los viewsets incluidos

core/
├── views.py                   - CustomTokenObtainPairView (solo login)
├── urls.py                    - LEGACY (vacío, comentarios)
├── models.py                  - Usuario, Rol, Permiso, RolPermiso
├── serializers.py             - Todos los serializers
├── admin.py                   - Admin adaptado
└── tests.py                   - Tests completos
```

### Ventajas

✅ Todo centralizado en `api/`  
✅ Una sola línea en `config/urls.py`  
✅ Fácil de mantener y escalar  
✅ 118+ rutas organizadas  
✅ Viewsets en una ubicación clara  
✅ Auth integrada en el router

---

## Configuración de frontend (JavaScript/React)

### Ejemplo con fetch

```javascript
// Login
async function login(run, password) {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run, password }),
  });
  const data = await response.json();

  // Guardar tokens en localStorage
  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  localStorage.setItem("user", JSON.stringify(data.user));

  return data;
}

// Petición autenticada
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem("access_token");

  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  // Si token expiró (401), refrescar
  if (response.status === 401) {
    const refreshToken = localStorage.getItem("refresh_token");
    const refreshResponse = await fetch("/api/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    const refreshData = await refreshResponse.json();
    localStorage.setItem("access_token", refreshData.access);

    // Reintentar request original
    response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${refreshData.access}`,
      },
    });
  }

  return response;
}

// Uso
const usuarios = await fetchWithAuth("/api/usuarios/");
```

---

## Archivos modificados

| Archivo               | Cambios                                                             |
| --------------------- | ------------------------------------------------------------------- |
| `core/models.py`      | Usuario basado en AbstractUser, UsuarioManager, Rol con get_group() |
| `core/views.py`       | CustomTokenObtainPairView (solo login JWT)                          |
| `core/serializers.py` | LoginSerializer, ChangePasswordSerializer, UsuarioProfileSerializer |
| `core/urls.py`        | LEGACY: Vacío (URLs movidas a api/routers.py)                       |
| `core/admin.py`       | UsuarioAdmin adaptado a AbstractUser                                |
| `core/tests.py`       | Tests completos de autenticación                                    |
| `api/viewsets.py`     | **Centralizado**: Todos los viewsets incluidos                      |
| `api/routers.py`      | **Centralizado**: Router con URLs JWT + todos los viewsets          |
| `api/urls.py`         | **Simplificado**: Importa urlpatterns del router                    |
| `config/urls.py`      | **Simplificado**: Una sola línea `/api/`                            |
| `config/settings.py`  | AUTH_USER_MODEL, SIMPLE_JWT, REST_FRAMEWORK con JWTAuthentication   |
| `requirements.txt`    | Añadido djangorestframework-simplejwt==5.5.1                        |

---

## Ejecutar tests

```bash
# Todos los tests de core
python manage.py test core

# Solo tests de autenticación
python manage.py test core.tests.UsuarioAuthenticationAPITest

# Con verbosidad
python manage.py test core -v 2
```

---

## Seguridad recomendada

1. **En producción**, usar variables de entorno para `SECRET_KEY`:

   ```python
   SIMPLE_JWT = {
       'SIGNING_KEY': SECRET_KEY,
       ...
   }
   ```

2. **CORS**: Configurar orígenes permitidos en `.env`:

   ```
   CORS_ALLOW_ALL_ORIGINS=False
   CORS_ALLOWED_ORIGINS=http://localhost:3000,https://tudominio.com
   ```

3. **HTTPS**: Forzar en producción (`DEBUG=False`):

   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

4. **Rotación de tokens**: Ya configurada:
   ```python
   ROTATE_REFRESH_TOKENS = True
   BLACKLIST_AFTER_ROTATION = True
   ```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'rest_framework_simplejwt'"

```bash
pip install djangorestframework-simplejwt==5.5.1
```

### Error: "AttributeError: 'Usuario' object has no attribute 'username'"

- Es normal, ahora usa `run` como identificador
- Actualiza código que referenciaba `user.username` a `user.run`

### Token expirado (401 Unauthorized)

- Refrescar token con `/api/auth/token/refresh/`
- O volver a loguear

### No se puede loguear con credenciales antiguas

- Si migraste datos, asegúrate que las contraseñas se hasharon correctamente
- O crea nuevo superusuario y reinicia con contraseñas nuevas

---

## Próximos pasos opcionales

1. **Token Blacklist**: Para logout verdadero, instala `rest_framework_simplejwt[blacklist]`
2. **Social Auth**: Integrar Google/Microsoft con `django-allauth`
3. **2FA**: Autenticación de dos factores
4. **Permissions**: Sistema de permisos granulares con `RolPermiso`
5. **Swagger/OpenAPI**: Documentación automática de API con `drf-spectacular`
6. **Rate Limiting**: Límite de intentos con `django-ratelimit`

---

## Cambios recientes (v1.1)

✅ URLs centralizadas en `api/routers.py`  
✅ Estructura simplificada en `config/urls.py`  
✅ `core/urls.py` deprecado (legacy)  
✅ Todos los viewsets en `api/viewsets.py`  
✅ 118+ rutas organizadas y funcionales

---

**Versión**: 1.1  
**Fecha**: 15 de noviembre de 2025  
**Autor**: Sistema de autenticación JWT  
**Estado**: Listo para producción ✅
