from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Core
from core.models import Usuario, Rol, Permiso, RolPermiso
from core.serializers import UsuarioSerializer, RolSerializer, PermisoSerializer, RolPermisoSerializer

# Catalogs
from catalogs.models import CatNacionalidad, CatPuebloOriginario, CatComplicacionParto, CatRobson, CatTipoParto
from catalogs.serializers import CatNacionalidadSerializer, CatPuebloOriginarioSerializer, CatComplicacionPartoSerializer, CatRobsonSerializer, CatTipoPartoSerializer

# Maternity
from maternity.models import MadrePaciente, Embarazo, Parto, PartoComplicacion, PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo
from maternity.serializers import MadrePacienteSerializer, EmbarazoSerializer, PartoSerializer, PartoComplicacionSerializer, PartoAnestesiaSerializer, IVEAtencionSerializer, IVEAcompanamientoSerializer, AltaAnticonceptivoSerializer

# Neonatology
from neonatology.models import RecienNacido, RNAtencionInmediata, RNTamizajeMetabolico, RNTamizajeAuditivo, RNTamizajeCardiopatia, RNEgreso
from neonatology.serializers import RecienNacidoSerializer, RNAtencionInmediataSerializer, RNTamizajeMetabolicoSerializer, RNTamizajeAuditivoSerializer, RNTamizajeCardiopatiaSerializer, RNEgresoSerializer

# Compliance
from compliance.models import TrazaMovimiento
from compliance.serializers import TrazaMovimientoSerializer

# Alerts
from alerts.models import AlertaSistema
from alerts.serializers import AlertaSistemaSerializer

# Reports
from reports.models import ReporteREM, ReporteREMDetalle
from reports.serializers import ReporteREMSerializer, ReporteREMDetalleSerializer


# ============ CORE ViewSets ============
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]


class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]


class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated]


# ============ CATALOGS ViewSets ============
class CatNacionalidadViewSet(viewsets.ModelViewSet):
    queryset = CatNacionalidad.objects.all()
    serializer_class = CatNacionalidadSerializer
    permission_classes = [IsAuthenticated]


class CatPuebloOriginarioViewSet(viewsets.ModelViewSet):
    queryset = CatPuebloOriginario.objects.all()
    serializer_class = CatPuebloOriginarioSerializer
    permission_classes = [IsAuthenticated]


class CatComplicacionPartoViewSet(viewsets.ModelViewSet):
    queryset = CatComplicacionParto.objects.all()
    serializer_class = CatComplicacionPartoSerializer
    permission_classes = [IsAuthenticated]


class CatRobsonViewSet(viewsets.ModelViewSet):
    queryset = CatRobson.objects.all()
    serializer_class = CatRobsonSerializer
    permission_classes = [IsAuthenticated]


class CatTipoPartoViewSet(viewsets.ModelViewSet):
    queryset = CatTipoParto.objects.all()
    serializer_class = CatTipoPartoSerializer
    permission_classes = [IsAuthenticated]


# ============ MATERNITY ViewSets ============
class MadrePacienteViewSet(viewsets.ModelViewSet):
    queryset = MadrePaciente.objects.all()
    serializer_class = MadrePacienteSerializer
    permission_classes = [IsAuthenticated]


class EmbarazoViewSet(viewsets.ModelViewSet):
    queryset = Embarazo.objects.all()
    serializer_class = EmbarazoSerializer
    permission_classes = [IsAuthenticated]


class PartoViewSet(viewsets.ModelViewSet):
    queryset = Parto.objects.all()
    serializer_class = PartoSerializer
    permission_classes = [IsAuthenticated]


class PartoComplicacionViewSet(viewsets.ModelViewSet):
    queryset = PartoComplicacion.objects.all()
    serializer_class = PartoComplicacionSerializer
    permission_classes = [IsAuthenticated]


class PartoAnestesiaViewSet(viewsets.ModelViewSet):
    queryset = PartoAnestesia.objects.all()
    serializer_class = PartoAnestesiaSerializer
    permission_classes = [IsAuthenticated]


class IVEAtencionViewSet(viewsets.ModelViewSet):
    queryset = IVEAtencion.objects.all()
    serializer_class = IVEAtencionSerializer
    permission_classes = [IsAuthenticated]


class IVEAcompanamientoViewSet(viewsets.ModelViewSet):
    queryset = IVEAcompanamiento.objects.all()
    serializer_class = IVEAcompanamientoSerializer
    permission_classes = [IsAuthenticated]


class AltaAnticonceptivoViewSet(viewsets.ModelViewSet):
    queryset = AltaAnticonceptivo.objects.all()
    serializer_class = AltaAnticonceptivoSerializer
    permission_classes = [IsAuthenticated]


# ============ NEONATOLOGY ViewSets ============
class RecienNacidoViewSet(viewsets.ModelViewSet):
    queryset = RecienNacido.objects.all()
    serializer_class = RecienNacidoSerializer
    permission_classes = [IsAuthenticated]


class RNAtencionInmediataViewSet(viewsets.ModelViewSet):
    queryset = RNAtencionInmediata.objects.all()
    serializer_class = RNAtencionInmediataSerializer
    permission_classes = [IsAuthenticated]


class RNTamizajeMetabolicoViewSet(viewsets.ModelViewSet):
    queryset = RNTamizajeMetabolico.objects.all()
    serializer_class = RNTamizajeMetabolicoSerializer
    permission_classes = [IsAuthenticated]


class RNTamizajeAuditivoViewSet(viewsets.ModelViewSet):
    queryset = RNTamizajeAuditivo.objects.all()
    serializer_class = RNTamizajeAuditivoSerializer
    permission_classes = [IsAuthenticated]


class RNTamizajeCardiopatiaViewSet(viewsets.ModelViewSet):
    queryset = RNTamizajeCardiopatia.objects.all()
    serializer_class = RNTamizajeCardiopatiaSerializer
    permission_classes = [IsAuthenticated]


class RNEgresoViewSet(viewsets.ModelViewSet):
    queryset = RNEgreso.objects.all()
    serializer_class = RNEgresoSerializer
    permission_classes = [IsAuthenticated]


# ============ COMPLIANCE ViewSets ============
class TrazaMovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrazaMovimiento.objects.all()
    serializer_class = TrazaMovimientoSerializer
    permission_classes = [IsAuthenticated]


# ============ ALERTS ViewSets ============
class AlertaSistemaViewSet(viewsets.ModelViewSet):
    queryset = AlertaSistema.objects.all()
    serializer_class = AlertaSistemaSerializer
    permission_classes = [IsAuthenticated]


# ============ REPORTS ViewSets ============
class ReporteREMViewSet(viewsets.ModelViewSet):
    queryset = ReporteREM.objects.all()
    serializer_class = ReporteREMSerializer
    permission_classes = [IsAuthenticated]


class ReporteREMDetalleViewSet(viewsets.ModelViewSet):
    queryset = ReporteREMDetalle.objects.all()
    serializer_class = ReporteREMDetalleSerializer
    permission_classes = [IsAuthenticated]