"""
ViewSets con Sistema RBAC y Documentación drf-spectacular
Versión: 2.1 - Noviembre 2025
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# Importar utilidades de drf-spectacular
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

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

@extend_schema_view(
    list=extend_schema(tags=['Usuarios'], summary='Listar usuarios', description='Requiere: core:user:manage'),
    create=extend_schema(tags=['Usuarios'], summary='Crear usuario', description='Requiere: core:user:manage'),
    retrieve=extend_schema(tags=['Usuarios'], summary='Obtener usuario'),
    update=extend_schema(tags=['Usuarios'], summary='Actualizar usuario'),
    partial_update=extend_schema(tags=['Usuarios'], summary='Actualizar usuario (parcial)'),
    destroy=extend_schema(tags=['Usuarios'], summary='Eliminar usuario'),
)
class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios con permisos RBAC."""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return 'core:user:manage'
        return 'core:user:manage'
    
    def check_permissions(self, request):
        if self.action in ['me', 'change_password', 'logout']:
            return
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)

    @extend_schema(tags=['Usuarios'], summary='Mi perfil', description='Obtiene perfil del usuario autenticado')
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UsuarioProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(tags=['Usuarios'], summary='Cambiar contraseña')
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': 'Contraseña incorrecta'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Contraseña actualizada exitosamente'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=['Usuarios'], summary='Logout')
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        return Response({'detail': 'Logout exitoso'}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=['Roles & Permisos'], summary='Listar roles'),
    create=extend_schema(tags=['Roles & Permisos'], summary='Crear rol'),
    retrieve=extend_schema(tags=['Roles & Permisos'], summary='Obtener rol'),
    update=extend_schema(tags=['Roles & Permisos'], summary='Actualizar rol'),
    destroy=extend_schema(tags=['Roles & Permisos'], summary='Eliminar rol'),
)
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'core:role:manage'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Roles & Permisos'], summary='Listar permisos'),
    create=extend_schema(tags=['Roles & Permisos'], summary='Crear permiso'),
    retrieve=extend_schema(tags=['Roles & Permisos'], summary='Obtener permiso'),
    update=extend_schema(tags=['Roles & Permisos'], summary='Actualizar permiso'),
    destroy=extend_schema(tags=['Roles & Permisos'], summary='Eliminar permiso'),
)
class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'core:role:manage'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Roles & Permisos'], summary='Listar asignaciones rol-permiso'),
    create=extend_schema(tags=['Roles & Permisos'], summary='Asignar permiso a rol'),
    retrieve=extend_schema(tags=['Roles & Permisos'], summary='Obtener asignación'),
    destroy=extend_schema(tags=['Roles & Permisos'], summary='Eliminar asignación'),
)
class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'core:role:manage'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============ CATALOGS ViewSets ============

@extend_schema_view(
    list=extend_schema(tags=['Catálogos'], summary='Listar nacionalidades'),
    create=extend_schema(tags=['Catálogos'], summary='Crear nacionalidad'),
    retrieve=extend_schema(tags=['Catálogos'], summary='Obtener nacionalidad'),
    update=extend_schema(tags=['Catálogos'], summary='Actualizar nacionalidad'),
    destroy=extend_schema(tags=['Catálogos'], summary='Eliminar nacionalidad'),
)
class CatNacionalidadViewSet(viewsets.ModelViewSet):
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


@extend_schema_view(
    list=extend_schema(tags=['Catálogos'], summary='Listar pueblos originarios'),
    create=extend_schema(tags=['Catálogos'], summary='Crear pueblo originario'),
    retrieve=extend_schema(tags=['Catálogos'], summary='Obtener pueblo originario'),
    update=extend_schema(tags=['Catálogos'], summary='Actualizar pueblo originario'),
    destroy=extend_schema(tags=['Catálogos'], summary='Eliminar pueblo originario'),
)
class CatPuebloOriginarioViewSet(viewsets.ModelViewSet):
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


@extend_schema_view(
    list=extend_schema(tags=['Catálogos'], summary='Listar complicaciones de parto'),
    create=extend_schema(tags=['Catálogos'], summary='Crear complicación'),
    retrieve=extend_schema(tags=['Catálogos'], summary='Obtener complicación'),
    update=extend_schema(tags=['Catálogos'], summary='Actualizar complicación'),
    destroy=extend_schema(tags=['Catálogos'], summary='Eliminar complicación'),
)
class CatComplicacionPartoViewSet(viewsets.ModelViewSet):
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


@extend_schema_view(
    list=extend_schema(tags=['Catálogos'], summary='Listar clasificaciones Robson'),
    create=extend_schema(tags=['Catálogos'], summary='Crear clasificación Robson'),
    retrieve=extend_schema(tags=['Catálogos'], summary='Obtener clasificación Robson'),
    update=extend_schema(tags=['Catálogos'], summary='Actualizar clasificación Robson'),
    destroy=extend_schema(tags=['Catálogos'], summary='Eliminar clasificación Robson'),
)
class CatRobsonViewSet(viewsets.ModelViewSet):
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


@extend_schema_view(
    list=extend_schema(tags=['Catálogos'], summary='Listar tipos de parto'),
    create=extend_schema(tags=['Catálogos'], summary='Crear tipo de parto'),
    retrieve=extend_schema(tags=['Catálogos'], summary='Obtener tipo de parto'),
    update=extend_schema(tags=['Catálogos'], summary='Actualizar tipo de parto'),
    destroy=extend_schema(tags=['Catálogos'], summary='Eliminar tipo de parto'),
)
class CatTipoPartoViewSet(viewsets.ModelViewSet):
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

@extend_schema_view(
    list=extend_schema(
        tags=['Maternidad'], 
        summary='Listar madres pacientes',
        description='Retorna lista paginada de madres. Requiere: maternity:mother:read',
        parameters=[
            OpenApiParameter('run', str, description='Filtrar por RUN'),
            OpenApiParameter('fk_nacionalidad', int, description='Filtrar por nacionalidad'),
        ]
    ),
    create=extend_schema(tags=['Maternidad'], summary='Crear madre paciente', description='Requiere: maternity:mother:create'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener madre paciente'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar madre paciente'),
    partial_update=extend_schema(tags=['Maternidad'], summary='Actualizar madre (parcial)'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar madre paciente'),
)
class MadrePacienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de madres pacientes con permisos RBAC."""
    queryset = MadrePaciente.objects.all()
    serializer_class = MadrePacienteSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    search_fields = ['run', 'nombre', 'apellido_paterno', 'apellido_materno']
    filterset_fields = ['fk_nacionalidad', 'fk_pueblo_originario']
    
    def get_required_permission(self):
        if self.action == 'create':
            return 'maternity:mother:create'
        elif self.action in ['update', 'partial_update']:
            return 'maternity:mother:update'
        elif self.action == 'destroy':
            return 'maternity:mother:update'
        return 'maternity:mother:read'
    
    def check_permissions(self, request):
        if self.action in ['embarazos', 'partos', 'ive_atenciones']:
            self.required_permission = 'maternity:mother:read'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    @extend_schema(tags=['Maternidad'], summary='Obtener embarazos de una madre')
    @action(detail=True, methods=['get'])
    def embarazos(self, request, pk=None):
        madre = self.get_object()
        embarazos = madre.embarazos.all()
        serializer = EmbarazoSerializer(embarazos, many=True)
        return Response(serializer.data)
    
    @extend_schema(tags=['Maternidad'], summary='Obtener partos de una madre')
    @action(detail=True, methods=['get'])
    def partos(self, request, pk=None):
        madre = self.get_object()
        partos = madre.partos.all()
        serializer = PartoDetailSerializer(partos, many=True)
        return Response(serializer.data)
    
    @extend_schema(tags=['Maternidad'], summary='Obtener atenciones IVE de una madre')
    @action(detail=True, methods=['get'])
    def ive_atenciones(self, request, pk=None):
        madre = self.get_object()
        ives = madre.ive_atenciones.all()
        serializer = IVEAtencionDetailSerializer(ives, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Maternidad'], summary='Listar embarazos'),
    create=extend_schema(tags=['Maternidad'], summary='Crear embarazo'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener embarazo'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar embarazo'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar embarazo'),
)
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
    
    @extend_schema(tags=['Maternidad'], summary='Obtener detalle de embarazo con trimestre y viabilidad')
    @action(detail=True, methods=['get'])
    def detalle(self, request, pk=None):
        embarazo = self.get_object()
        return Response({
            'id': embarazo.id_embarazo,
            'madre': MadrePacienteSerializer(embarazo.fk_madre).data,
            'semana_obstetrica': embarazo.semana_obstetrica,
            'trimestre': embarazo.obtener_trimestre(),
            'viable': embarazo.es_embarazo_viables(),
            'fecha_ultima_menstruacion': embarazo.fecha_ultima_menstruacion,
        })


@extend_schema_view(
    list=extend_schema(
        tags=['Maternidad'], 
        summary='Listar partos',
        description='Requiere: maternity:delivery:read. Matronas con restricción de turno.',
        parameters=[
            OpenApiParameter('fk_madre', int, description='Filtrar por madre'),
            OpenApiParameter('fk_tipo_parto', int, description='Filtrar por tipo de parto'),
        ]
    ),
    create=extend_schema(tags=['Maternidad'], summary='Crear parto', description='Requiere: maternity:delivery:create'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener parto (detalle completo)'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar parto'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar parto'),
)
class PartoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de partos con permisos RBAC y restricción de turno."""
    queryset = Parto.objects.all()
    serializer_class = PartoDetailSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_madre', 'fk_tipo_parto']
    ordering_fields = ['fecha_parto', 'fecha_registro']
    
    def get_required_permission(self):
        if self.action == 'create':
            return 'maternity:delivery:create'
        elif self.action in ['update', 'partial_update']:
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
        return puede_modificar_registro_turno(usuario, obj)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PartoDetailSerializer
        return PartoSerializer
    
    @extend_schema(tags=['Maternidad'], summary='Obtener complicaciones de un parto')
    @action(detail=True, methods=['get'])
    def complicaciones(self, request, pk=None):
        parto = self.get_object()
        complicaciones = parto.complicaciones.all()
        serializer = PartoComplicacionSerializer(complicaciones, many=True)
        return Response({
            'parto_id': parto.id_parto,
            'tuvo_complicaciones': parto.tuvo_complicaciones(),
            'complicaciones': serializer.data
        })
    
    @extend_schema(tags=['Maternidad'], summary='Obtener anestesias de un parto')
    @action(detail=True, methods=['get'])
    def anestesias(self, request, pk=None):
        parto = self.get_object()
        anestesias = parto.anestesias.all()
        serializer = PartoAnestesiaSerializer(anestesias, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Maternidad'], summary='Listar complicaciones de parto'),
    create=extend_schema(tags=['Maternidad'], summary='Crear complicación de parto'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener complicación'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar complicación'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar complicación'),
)
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
    
    @extend_schema(
        tags=['Maternidad'], 
        summary='Obtener complicaciones por parto',
        parameters=[OpenApiParameter('parto_id', int, required=True, description='ID del parto')]
    )
    @action(detail=False, methods=['get'])
    def por_parto(self, request):
        from rest_framework.exceptions import ValidationError
        parto_id = request.query_params.get('parto_id')
        if not parto_id:
            raise ValidationError({'parto_id': 'Este parámetro es requerido'})
        complicaciones = self.queryset.filter(fk_parto=parto_id)
        serializer = self.get_serializer(complicaciones, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Maternidad'], summary='Listar anestesias de parto'),
    create=extend_schema(tags=['Maternidad'], summary='Crear anestesia'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener anestesia'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar anestesia'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar anestesia'),
)
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
    
    @extend_schema(tags=['Maternidad'], summary='Estadísticas de tipos de anestesia')
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        from django.db.models import Count
        stats = PartoAnestesia.objects.values('tipo_anestesia').annotate(cantidad=Count('id_anestesia'))
        return Response(list(stats))


@extend_schema_view(
    list=extend_schema(tags=['Maternidad'], summary='Listar atenciones IVE'),
    create=extend_schema(tags=['Maternidad'], summary='Crear atención IVE'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener atención IVE (con acompañamientos)'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar atención IVE'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar atención IVE'),
)
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
    
    @extend_schema(tags=['Maternidad'], summary='Obtener acompañamientos de una atención IVE')
    @action(detail=True, methods=['get'])
    def acompaniamientos(self, request, pk=None):
        ive = self.get_object()
        acomps = ive.acompañamientos.all()
        serializer = IVEAcompanamientoSerializer(acomps, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Maternidad'], summary='Listar acompañamientos IVE'),
    create=extend_schema(tags=['Maternidad'], summary='Crear acompañamiento IVE'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener acompañamiento IVE'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar acompañamiento IVE'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar acompañamiento IVE'),
)
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
    
    @extend_schema(tags=['Maternidad'], summary='Obtener tipos de profesionales disponibles')
    @action(detail=False, methods=['get'])
    def tipos_disponibles(self, request):
        tipos = IVEAcompanamiento.TIPO_PROFESIONAL_CHOICES
        return Response([{'value': t[0], 'label': t[1]} for t in tipos])


@extend_schema_view(
    list=extend_schema(tags=['Maternidad'], summary='Listar altas anticonceptivas'),
    create=extend_schema(tags=['Maternidad'], summary='Crear alta anticonceptiva'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener alta anticonceptiva'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar alta anticonceptiva'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar alta anticonceptiva'),
)
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

@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar recién nacidos'),
    create=extend_schema(tags=['Neonatología'], summary='Crear recién nacido', description='Requiere: neonatal:rn:create'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener recién nacido'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar recién nacido'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar recién nacido'),
)
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


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar atenciones inmediatas RN'),
    create=extend_schema(tags=['Neonatología'], summary='Crear atención inmediata RN', description='Requiere: neonatal:rn:update_immediate'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener atención inmediata RN'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar atención inmediata RN'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar atención inmediata RN'),
)
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


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar tamizajes metabólicos'),
    create=extend_schema(tags=['Neonatología'], summary='Crear tamizaje metabólico', description='Requiere: neonatal:tamizaje:manage'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener tamizaje metabólico'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar tamizaje metabólico'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar tamizaje metabólico'),
)
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


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar tamizajes auditivos'),
    create=extend_schema(tags=['Neonatología'], summary='Crear tamizaje auditivo', description='Requiere: neonatal:tamizaje:manage'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener tamizaje auditivo'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar tamizaje auditivo'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar tamizaje auditivo'),
)
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


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar tamizajes de cardiopatías'),
    create=extend_schema(tags=['Neonatología'], summary='Crear tamizaje de cardiopatía', description='Requiere: neonatal:tamizaje:manage'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener tamizaje de cardiopatía'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar tamizaje de cardiopatía'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar tamizaje de cardiopatía'),
)
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


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar egresos de RN'),
    create=extend_schema(tags=['Neonatología'], summary='Crear egreso de RN', description='Requiere: neonatal:discharge:manage'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener egreso de RN'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar egreso de RN'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar egreso de RN'),
)
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

@extend_schema_view(
    list=extend_schema(
        tags=['Auditoría'], 
        summary='Listar trazas de auditoría', 
        description='Solo lectura. Requiere: compliance:audit:read (solo supervisores)',
        parameters=[
            OpenApiParameter('tipo_accion', str, description='Filtrar por tipo de acción'),
            OpenApiParameter('tabla_afectada', str, description='Filtrar por tabla afectada'),
        ]
    ),
    retrieve=extend_schema(tags=['Auditoría'], summary='Obtener traza de auditoría'),
)
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

@extend_schema_view(
    list=extend_schema(tags=['Alertas'], summary='Listar alertas del sistema', description='Requiere: alert:read'),
    create=extend_schema(tags=['Alertas'], summary='Crear alerta', description='Requiere: alert:resolve'),
    retrieve=extend_schema(tags=['Alertas'], summary='Obtener alerta'),
    update=extend_schema(tags=['Alertas'], summary='Actualizar alerta (resolver)', description='Requiere: alert:resolve'),
    partial_update=extend_schema(tags=['Alertas'], summary='Actualizar alerta parcialmente'),
    destroy=extend_schema(tags=['Alertas'], summary='Eliminar alerta', description='Requiere: alert:resolve'),
)
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

@extend_schema_view(
    list=extend_schema(
        tags=['Reportes'], 
        summary='Listar reportes REM', 
        description='Requiere: report:generate_rem (solo supervisores)'
    ),
    create=extend_schema(tags=['Reportes'], summary='Generar reporte REM', description='Requiere: report:generate_rem'),
    retrieve=extend_schema(tags=['Reportes'], summary='Obtener reporte REM'),
    update=extend_schema(tags=['Reportes'], summary='Actualizar reporte REM'),
    destroy=extend_schema(tags=['Reportes'], summary='Eliminar reporte REM'),
)
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
        return 'report:generate_rem'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Reportes'], summary='Listar detalles de reportes REM'),
    create=extend_schema(tags=['Reportes'], summary='Crear detalle de reporte REM'),
    retrieve=extend_schema(tags=['Reportes'], summary='Obtener detalle de reporte REM'),
    update=extend_schema(tags=['Reportes'], summary='Actualizar detalle de reporte REM'),
    destroy=extend_schema(tags=['Reportes'], summary='Eliminar detalle de reporte REM'),
)
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