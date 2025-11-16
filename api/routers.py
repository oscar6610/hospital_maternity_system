from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import CustomTokenObtainPairView
from .viewsets import (
    # Core
    UsuarioViewSet, RolViewSet, PermisoViewSet, RolPermisoViewSet,
    # Catalogs
    CatNacionalidadViewSet, CatPuebloOriginarioViewSet, CatComplicacionPartoViewSet,
    CatRobsonViewSet, CatTipoPartoViewSet,
    # Maternity
    MadrePacienteViewSet, EmbarazoViewSet, PartoViewSet, PartoComplicacionViewSet,
    PartoAnestesiaViewSet, IVEAtencionViewSet, IVEAcompanamientoViewSet, AltaAnticonceptivoViewSet,
    # Neonatology
    RecienNacidoViewSet, RNAtencionInmediataViewSet, RNTamizajeMetabolicoViewSet,
    RNTamizajeAuditivoViewSet, RNTamizajeCardiopatiaViewSet, RNEgresoViewSet,
    # Compliance
    TrazaMovimientoViewSet,
    # Alerts
    AlertaSistemaViewSet,
    # Reports
    ReporteREMViewSet, ReporteREMDetalleViewSet,
)

router = DefaultRouter()

# ============ CORE ============
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'permisos', PermisoViewSet, basename='permiso')
router.register(r'roles-permisos', RolPermisoViewSet, basename='rol-permiso')

# ============ CATALOGS ============
router.register(r'catalogs/nacionalidades', CatNacionalidadViewSet, basename='cat-nacionalidad')
router.register(r'catalogs/pueblos-originarios', CatPuebloOriginarioViewSet, basename='cat-pueblo-originario')
router.register(r'catalogs/complicaciones-parto', CatComplicacionPartoViewSet, basename='cat-complicacion-parto')
router.register(r'catalogs/robson', CatRobsonViewSet, basename='cat-robson')
router.register(r'catalogs/tipos-parto', CatTipoPartoViewSet, basename='cat-tipo-parto')

# ============ MATERNITY ============
router.register(r'maternity/madres', MadrePacienteViewSet, basename='madre-paciente')
router.register(r'maternity/embarazos', EmbarazoViewSet, basename='embarazo')
router.register(r'maternity/partos', PartoViewSet, basename='parto')
router.register(r'maternity/partos-complicaciones', PartoComplicacionViewSet, basename='parto-complicacion')
router.register(r'maternity/partos-anestesias', PartoAnestesiaViewSet, basename='parto-anestesia')
router.register(r'maternity/ive-atenciones', IVEAtencionViewSet, basename='ive-atencion')
router.register(r'maternity/ive-acompanamientos', IVEAcompanamientoViewSet, basename='ive-acompanamiento')
router.register(r'maternity/altas-anticonceptivos', AltaAnticonceptivoViewSet, basename='alta-anticonceptivo')

# ============ NEONATOLOGY ============
router.register(r'neonatology/recien-nacidos', RecienNacidoViewSet, basename='recien-nacido')
router.register(r'neonatology/atenciones-inmediatas', RNAtencionInmediataViewSet, basename='rn-atencion-inmediata')
router.register(r'neonatology/tamizajes-metabolicos', RNTamizajeMetabolicoViewSet, basename='rn-tamizaje-metabolico')
router.register(r'neonatology/tamizajes-auditivos', RNTamizajeAuditivoViewSet, basename='rn-tamizaje-auditivo')
router.register(r'neonatology/tamizajes-cardiopatias', RNTamizajeCardiopatiaViewSet, basename='rn-tamizaje-cardiopatia')
router.register(r'neonatology/egresos', RNEgresoViewSet, basename='rn-egreso')

# ============ COMPLIANCE ============
router.register(r'compliance/trazas', TrazaMovimientoViewSet, basename='traza-movimiento')

# ============ ALERTS ============
router.register(r'alerts/alertas', AlertaSistemaViewSet, basename='alerta-sistema')

# ============ REPORTS ============
router.register(r'reports/reportes-rem', ReporteREMViewSet, basename='reporte-rem')
router.register(r'reports/reportes-rem-detalles', ReporteREMDetalleViewSet, basename='reporte-rem-detalle')

# ============ AUTHENTICATION (JWT) ============
auth_urls = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Combinar URLs de autenticación con el router
urlpatterns = auth_urls + router.urls