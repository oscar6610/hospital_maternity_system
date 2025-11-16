from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# Core
from core.models import Usuario, Rol, Permiso, RolPermiso
from core.serializers import (
    UsuarioSerializer, RolSerializer, PermisoSerializer, RolPermisoSerializer,
    LoginSerializer, ChangePasswordSerializer, UsuarioProfileSerializer
)

# Catalogs
from catalogs.models import CatNacionalidad, CatPuebloOriginario, CatComplicacionParto, CatRobson, CatTipoParto
from catalogs.serializers import CatNacionalidadSerializer, CatPuebloOriginarioSerializer, CatComplicacionPartoSerializer, CatRobsonSerializer, CatTipoPartoSerializer

# Maternity
from maternity.models import MadrePaciente, Embarazo, Parto, PartoComplicacion, PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo
from maternity.serializers import (
    MadrePacienteSerializer, EmbarazoSerializer, PartoSerializer, PartoDetailSerializer,
    PartoComplicacionSerializer, PartoAnestesiaSerializer, 
    IVEAtencionSerializer, IVEAtencionDetailSerializer, IVEAcompanamientoSerializer, 
    AltaAnticonceptivoSerializer
)

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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtener perfil del usuario autenticado"""
        serializer = UsuarioProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Cambiar contraseña del usuario autenticado"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Contraseña incorrecta'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Contraseña actualizada exitosamente'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout - simplemente retorna un mensaje confirmando logout"""
        return Response({'detail': 'Logout exitoso'}, status=status.HTTP_200_OK)


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
    search_fields = ['run', 'nombre', 'apellido_paterno', 'apellido_materno']
    filterset_fields = ['fk_nacionalidad', 'fk_pueblo_originario']
    
    @action(detail=True, methods=['get'])
    def embarazos(self, request, pk=None):
        """Obtiene todos los embarazos de una madre."""
        madre = self.get_object()
        embarazos = madre.embarazos.all()
        serializer = EmbarazoSerializer(embarazos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def partos(self, request, pk=None):
        """Obtiene todos los partos de una madre."""
        madre = self.get_object()
        partos = madre.partos.all()
        serializer = PartoDetailSerializer(partos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ive_atenciones(self, request, pk=None):
        """Obtiene todas las atenciones IVE de una madre."""
        madre = self.get_object()
        ives = madre.ive_atenciones.all()
        serializer = IVEAtencionDetailSerializer(ives, many=True)
        return Response(serializer.data)


class EmbarazoViewSet(viewsets.ModelViewSet):
    queryset = Embarazo.objects.all()
    serializer_class = EmbarazoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fk_madre']
    ordering_fields = ['semana_obstetrica', 'fecha_registro']
    
    @action(detail=True, methods=['get'])
    def detalle(self, request, pk=None):
        """Obtiene detalle del embarazo con trimestre y viabilidad."""
        embarazo = self.get_object()
        return Response({
            'id': embarazo.id_embarazo,
            'madre': MadrePacienteSerializer(embarazo.fk_madre).data,
            'semana_obstetrica': embarazo.semana_obstetrica,
            'trimestre': embarazo.obtener_trimestre(),
            'viable': embarazo.es_embarazo_viables(),
            'fecha_ultima_menstruacion': embarazo.fecha_ultima_menstruacion,
        })


class PartoViewSet(viewsets.ModelViewSet):
    queryset = Parto.objects.all()
    serializer_class = PartoDetailSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fk_madre', 'fk_tipo_parto']
    ordering_fields = ['fecha_parto', 'fecha_registro']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PartoDetailSerializer
        return PartoSerializer
    
    @action(detail=True, methods=['get'])
    def complicaciones(self, request, pk=None):
        """Obtiene todas las complicaciones de un parto."""
        parto = self.get_object()
        complicaciones = parto.complicaciones.all()
        serializer = PartoComplicacionSerializer(complicaciones, many=True)
        return Response({
            'parto_id': parto.id_parto,
            'tuvo_complicaciones': parto.tuvo_complicaciones(),
            'complicaciones': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def anestesias(self, request, pk=None):
        """Obtiene todas las anestesias de un parto."""
        parto = self.get_object()
        anestesias = parto.anestesias.all()
        serializer = PartoAnestesiaSerializer(anestesias, many=True)
        return Response(serializer.data)


class PartoComplicacionViewSet(viewsets.ModelViewSet):
    queryset = PartoComplicacion.objects.all()
    serializer_class = PartoComplicacionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fk_parto', 'fk_complicacion']
    
    @action(detail=False, methods=['get'])
    def por_parto(self, request):
        """Agrupa complicaciones por parto."""
        from django.db.models import Count
        from rest_framework.exceptions import ValidationError
        
        parto_id = request.query_params.get('parto_id')
        if not parto_id:
            raise ValidationError({'parto_id': 'Este parámetro es requerido'})
        
        complicaciones = self.queryset.filter(fk_parto=parto_id)
        serializer = self.get_serializer(complicaciones, many=True)
        return Response(serializer.data)


class PartoAnestesiaViewSet(viewsets.ModelViewSet):
    queryset = PartoAnestesia.objects.all()
    serializer_class = PartoAnestesiaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fk_parto', 'tipo_anestesia']
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de tipos de anestesia."""
        from django.db.models import Count
        
        stats = PartoAnestesia.objects.values('tipo_anestesia').annotate(
            cantidad=Count('id_anestesia')
        )
        return Response(list(stats))


class IVEAtencionViewSet(viewsets.ModelViewSet):
    queryset = IVEAtencion.objects.all()
    serializer_class = IVEAtencionDetailSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fk_madre', 'fk_causal']
    ordering_fields = ['fecha_atencion']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IVEAtencionDetailSerializer
        return IVEAtencionSerializer
    
    @action(detail=True, methods=['get'])
    def acompaniamientos(self, request, pk=None):
        """Obtiene todos los acompañamientos de una atención IVE."""
        ive = self.get_object()
        acomps = ive.acompañamientos.all()
        serializer = IVEAcompanamientoSerializer(acomps, many=True)
        return Response(serializer.data)


class IVEAcompanamientoViewSet(viewsets.ModelViewSet):
    queryset = IVEAcompanamiento.objects.all()
    serializer_class = IVEAcompanamientoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['fk_ive_atencion', 'tipo_profesional']
    
    @action(detail=False, methods=['get'])
    def tipos_disponibles(self, request):
        """Retorna los tipos de profesionales disponibles."""
        tipos = IVEAcompanamiento.TIPO_PROFESIONAL_CHOICES
        return Response([{'value': t[0], 'label': t[1]} for t in tipos])


class AltaAnticonceptivoViewSet(viewsets.ModelViewSet):
    queryset = AltaAnticonceptivo.objects.all()
    serializer_class = AltaAnticonceptivoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo_alta', 'esterilizacion_quirurgica']
    ordering_fields = ['fecha_registro']


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