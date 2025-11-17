"""
ViewSets con Sistema RBAC (Role-Based Access Control) Implementado
Versión: 2.0 - Noviembre 2025
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# Importar permisos RBAC
from core.rbac_utils import RBACPermission, RBACObjectPermission, puede_modificar_registro_turno

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
    """ViewSet para gestión de usuarios con permisos RBAC."""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        """Permisos dinámicos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'core:user:manage'
        return 'core:user:manage'  # Solo supervisores pueden ver usuarios
    
    def check_permissions(self, request):
        """Override para usar el permiso dinámico."""
        # Las acciones 'me', 'change_password' y 'logout' no requieren permiso especial
        if self.action in ['me', 'change_password', 'logout']:
            return
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtener perfil del usuario autenticado (sin restricción RBAC)."""
        serializer = UsuarioProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Cambiar contraseña del usuario autenticado (sin restricción RBAC)."""
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
        """Logout - simplemente retorna un mensaje confirmando logout."""
        return Response({'detail': 'Logout exitoso'}, status=status.HTTP_200_OK)


class RolViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de roles con permisos RBAC."""
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        """Permisos dinámicos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'core:role:manage'
        return 'core:role:manage'  # Lectura también requiere permiso
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class PermisoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de permisos con permisos RBAC."""
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        """Permisos dinámicos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'core:role:manage'
        return 'core:role:manage'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class RolPermisoViewSet(viewsets.ModelViewSet):
    """ViewSet para asignación de permisos a roles."""
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'core:role:manage'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ CATALOGS ViewSets ============
class CatNacionalidadViewSet(viewsets.ModelViewSet):
    """ViewSet para catálogo de nacionalidades."""
    queryset = CatNacionalidad.objects.all()
    serializer_class = CatNacionalidadSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'catalog:manage'
        return 'catalog:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class CatPuebloOriginarioViewSet(viewsets.ModelViewSet):
    """ViewSet para catálogo de pueblos originarios."""
    queryset = CatPuebloOriginario.objects.all()
    serializer_class = CatPuebloOriginarioSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'catalog:manage'
        return 'catalog:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class CatComplicacionPartoViewSet(viewsets.ModelViewSet):
    """ViewSet para catálogo de complicaciones de parto."""
    queryset = CatComplicacionParto.objects.all()
    serializer_class = CatComplicacionPartoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'catalog:manage'
        return 'catalog:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class CatRobsonViewSet(viewsets.ModelViewSet):
    """ViewSet para clasificación de Robson."""
    queryset = CatRobson.objects.all()
    serializer_class = CatRobsonSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'catalog:manage'
        return 'catalog:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class CatTipoPartoViewSet(viewsets.ModelViewSet):
    """ViewSet para catálogo de tipos de parto."""
    queryset = CatTipoParto.objects.all()
    serializer_class = CatTipoPartoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'catalog:manage'
        return 'catalog:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ MATERNITY ViewSets ============
class MadrePacienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de madres pacientes con permisos RBAC."""
    queryset = MadrePaciente.objects.all()
    serializer_class = MadrePacienteSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    search_fields = ['run', 'nombre', 'apellido_paterno', 'apellido_materno']
    filterset_fields = ['fk_nacionalidad', 'fk_pueblo_originario']
    
    def get_required_permission(self):
        """Permisos dinámicos según la acción."""
        if self.action == 'create':
            return 'maternity:mother:create'
        elif self.action in ['update', 'partial_update']:
            return 'maternity:mother:update'
        elif self.action == 'destroy':
            return 'maternity:mother:update'  # No hay permiso delete específico
        return 'maternity:mother:read'
    
    def check_permissions(self, request):
        # Las acciones personalizadas usan el permiso de lectura
        if self.action in ['embarazos', 'partos', 'ive_atenciones']:
            self.required_permission = 'maternity:mother:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
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
    """ViewSet para gestión de embarazos con permisos RBAC."""
    queryset = Embarazo.objects.all()
    serializer_class = EmbarazoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['fk_madre']
    ordering_fields = ['semana_obstetrica', 'fecha_registro']
    
    def get_required_permission(self):
        if self.action == 'create':
            return 'maternity:mother:create'
        elif self.action in ['update', 'partial_update', 'destroy']:
            return 'maternity:mother:update'
        return 'maternity:mother:read'
    
    def check_permissions(self, request):
        if self.action == 'detalle':
            self.required_permission = 'maternity:mother:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
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
    """ViewSet para gestión de partos con permisos RBAC y restricción de turno."""
    queryset = Parto.objects.all()
    serializer_class = PartoDetailSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_madre', 'fk_tipo_parto']
    ordering_fields = ['fecha_parto', 'fecha_registro']
    
    def get_required_permission(self):
        """Permisos dinámicos según la acción."""
        if self.action == 'create':
            return 'maternity:delivery:create'
        elif self.action in ['update', 'partial_update']:
            # Si es matrona, necesita permiso update_own
            # Si es supervisor/médico, necesita update_all
            from core.rbac_utils import usuario_es_matrona
            if usuario_es_matrona(self.request.user):
                return 'maternity:delivery:update_own'
            return 'maternity:delivery:update_all'
        elif self.action == 'destroy':
            return 'maternity:delivery:update_all'
        return 'maternity:delivery:read'
    
    def check_permissions(self, request):
        if self.action in ['complicaciones', 'anestesias']:
            self.required_permission = 'maternity:delivery:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    def validar_permiso_objeto(self, usuario, obj):
        """Validación a nivel de objeto para restricción de turno."""
        return puede_modificar_registro_turno(usuario, obj)
    
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
    """ViewSet para gestión de complicaciones de parto con permisos RBAC."""
    queryset = PartoComplicacion.objects.all()
    serializer_class = PartoComplicacionSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['fk_parto', 'fk_complicacion']
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'maternity:complication:manage'
        return 'maternity:delivery:read'
    
    def check_permissions(self, request):
        if self.action == 'por_parto':
            self.required_permission = 'maternity:delivery:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    @action(detail=False, methods=['get'])
    def por_parto(self, request):
        """Agrupa complicaciones por parto."""
        from rest_framework.exceptions import ValidationError
        
        parto_id = request.query_params.get('parto_id')
        if not parto_id:
            raise ValidationError({'parto_id': 'Este parámetro es requerido'})
        
        complicaciones = self.queryset.filter(fk_parto=parto_id)
        serializer = self.get_serializer(complicaciones, many=True)
        return Response(serializer.data)


class PartoAnestesiaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de anestesias de parto con permisos RBAC."""
    queryset = PartoAnestesia.objects.all()
    serializer_class = PartoAnestesiaSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['fk_parto', 'tipo_anestesia']
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'maternity:delivery:update_all'
        return 'maternity:delivery:read'
    
    def check_permissions(self, request):
        if self.action == 'estadisticas':
            self.required_permission = 'maternity:delivery:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de tipos de anestesia."""
        from django.db.models import Count
        
        stats = PartoAnestesia.objects.values('tipo_anestesia').annotate(
            cantidad=Count('id_anestesia')
        )
        return Response(list(stats))


class IVEAtencionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de atenciones IVE con permisos RBAC."""
    queryset = IVEAtencion.objects.all()
    serializer_class = IVEAtencionDetailSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['fk_madre', 'fk_causal']
    ordering_fields = ['fecha_atencion']
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'maternity:ive:manage'
        return 'maternity:mother:read'
    
    def check_permissions(self, request):
        if self.action == 'acompaniamientos':
            self.required_permission = 'maternity:mother:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
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
    """ViewSet para gestión de acompañamientos IVE con permisos RBAC."""
    queryset = IVEAcompanamiento.objects.all()
    serializer_class = IVEAcompanamientoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['fk_ive_atencion', 'tipo_profesional']
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'maternity:ive:manage'
        return 'maternity:mother:read'
    
    def check_permissions(self, request):
        if self.action == 'tipos_disponibles':
            self.required_permission = 'maternity:mother:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    @action(detail=False, methods=['get'])
    def tipos_disponibles(self, request):
        """Retorna los tipos de profesionales disponibles."""
        tipos = IVEAcompanamiento.TIPO_PROFESIONAL_CHOICES
        return Response([{'value': t[0], 'label': t[1]} for t in tipos])


class AltaAnticonceptivoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de altas anticonceptivas con permisos RBAC."""
    queryset = AltaAnticonceptivo.objects.all()
    serializer_class = AltaAnticonceptivoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['tipo_alta', 'esterilizacion_quirurgica']
    ordering_fields = ['fecha_registro']
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'maternity:contraceptive:manage'
        return 'maternity:delivery:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ NEONATOLOGY ViewSets ============
class RecienNacidoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de recién nacidos con permisos RBAC."""
    queryset = RecienNacido.objects.all()
    serializer_class = RecienNacidoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action == 'create':
            return 'neonatal:rn:create'
        elif self.action in ['update', 'partial_update', 'destroy']:
            return 'neonatal:rn:update_immediate'
        return 'neonatal:rn:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class RNAtencionInmediataViewSet(viewsets.ModelViewSet):
    """ViewSet para atención inmediata de RN con permisos RBAC."""
    queryset = RNAtencionInmediata.objects.all()
    serializer_class = RNAtencionInmediataSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'neonatal:rn:update_immediate'
        return 'neonatal:rn:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class RNTamizajeMetabolicoViewSet(viewsets.ModelViewSet):
    """ViewSet para tamizaje metabólico de RN con permisos RBAC."""
    queryset = RNTamizajeMetabolico.objects.all()
    serializer_class = RNTamizajeMetabolicoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'neonatal:tamizaje:manage'
        return 'neonatal:rn:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class RNTamizajeAuditivoViewSet(viewsets.ModelViewSet):
    """ViewSet para tamizaje auditivo de RN con permisos RBAC."""
    queryset = RNTamizajeAuditivo.objects.all()
    serializer_class = RNTamizajeAuditivoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'neonatal:tamizaje:manage'
        return 'neonatal:rn:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class RNTamizajeCardiopatiaViewSet(viewsets.ModelViewSet):
    """ViewSet para tamizaje de cardiopatías de RN con permisos RBAC."""
    queryset = RNTamizajeCardiopatia.objects.all()
    serializer_class = RNTamizajeCardiopatiaSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'neonatal:tamizaje:manage'
        return 'neonatal:rn:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class RNEgresoViewSet(viewsets.ModelViewSet):
    """ViewSet para egreso de RN con permisos RBAC."""
    queryset = RNEgreso.objects.all()
    serializer_class = RNEgresoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'neonatal:discharge:manage'
        return 'neonatal:rn:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ COMPLIANCE ViewSets ============
class TrazaMovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para auditoría con permisos RBAC."""
    queryset = TrazaMovimiento.objects.all()
    serializer_class = TrazaMovimientoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'compliance:audit:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ ALERTS ViewSets ============
class AlertaSistemaViewSet(viewsets.ModelViewSet):
    """ViewSet para alertas del sistema con permisos RBAC."""
    queryset = AlertaSistema.objects.all()
    serializer_class = AlertaSistemaSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['update', 'partial_update']:
            return 'alert:resolve'
        elif self.action in ['create', 'destroy']:
            return 'alert:resolve'
        return 'alert:read'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ REPORTS ViewSets ============
class ReporteREMViewSet(viewsets.ModelViewSet):
    """ViewSet para reportes REM con permisos RBAC."""
    queryset = ReporteREM.objects.all()
    serializer_class = ReporteREMSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action == 'create':
            return 'report:generate_rem'
        elif self.action in ['update', 'partial_update', 'destroy']:
            return 'report:generate_rem'
        return 'report:generate_rem'  # Lectura también requiere permiso especial
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


class ReporteREMDetalleViewSet(viewsets.ModelViewSet):
    """ViewSet para detalles de reportes REM con permisos RBAC."""
    queryset = ReporteREMDetalle.objects.all()
    serializer_class = ReporteREMDetalleSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'report:generate_rem'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)