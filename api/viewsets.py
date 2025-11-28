"""
ViewSets con Sistema RBAC Nativo de Django
Versión: 3.0 - Noviembre 2025
Migrado a Permissions y Groups nativos
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# Importar utilidades de drf-spectacular
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

# Importar permisos RBAC nativos
from core.rbac_utils import RBACPermission, RBACObjectPermission, puede_modificar_registro_turno

# Core
from core.models import Usuario
from django.contrib.auth.models import Group, Permission
from core.serializers import (
    UsuarioSerializer, LoginSerializer, ChangePasswordSerializer, UsuarioProfileSerializer
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


# ============================================================
# CORE ViewSets
# ============================================================

@extend_schema_view(
    list=extend_schema(tags=['Usuarios'], summary='Listar usuarios', description='Requiere: core.view_usuario'),
    create=extend_schema(tags=['Usuarios'], summary='Crear usuario', description='Requiere: core.add_usuario'),
    retrieve=extend_schema(tags=['Usuarios'], summary='Obtener usuario'),
    update=extend_schema(tags=['Usuarios'], summary='Actualizar usuario'),
    partial_update=extend_schema(tags=['Usuarios'], summary='Actualizar usuario (parcial)'),
    destroy=extend_schema(tags=['Usuarios'], summary='Eliminar usuario'),
)
class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios con permisos nativos de Django."""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        """Retorna el permiso requerido según la acción."""
        if self.action == 'create':
            return 'core.add_usuario'
        elif self.action in ['update', 'partial_update']:
            return 'core.change_usuario'
        elif self.action == 'destroy':
            return 'core.delete_usuario'
        return 'core.view_usuario'
    
    def check_permissions(self, request):
        """Valida permisos antes de ejecutar la acción."""
        if self.action in ['me', 'change_password', 'logout']:
            # Estas acciones no requieren permisos especiales
            return
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)

    @extend_schema(tags=['Usuarios'], summary='Mi perfil', description='Obtiene perfil del usuario autenticado')
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.user.is_anonymous:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = UsuarioProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(tags=['Usuarios'], summary='Cambiar contraseña')
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change_password')
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
    
    def update(self, request, *args, **kwargs):
        """
        Override de update para invalidar tokens JWT cuando se cambia el grupo.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        instance = self.get_object()
        grupos_anteriores = set(instance.groups.values_list('id', flat=True))
        
        # Ejecutar la actualización normal
        response = super().update(request, *args, **kwargs)
        
        # Verificar si hubo cambio de grupos
        instance.refresh_from_db()
        grupos_nuevos = set(instance.groups.values_list('id', flat=True))
        cambio_de_grupos = grupos_anteriores != grupos_nuevos
        
        # Si hubo cambio de grupos exitoso, invalidar tokens
        if cambio_de_grupos and response.status_code in [200, 201]:
            try:
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
                
                tokens = OutstandingToken.objects.filter(user=instance)
                tokens_invalidados = 0
                
                for token in tokens:
                    try:
                        token.blacklist()
                        tokens_invalidados += 1
                    except Exception:
                        pass
                
                logger.info(
                    f"✓ Usuario {instance.run} cambió de grupos. "
                    f"Tokens invalidados: {tokens_invalidados}"
                )
                
                if isinstance(response.data, dict):
                    response.data['_security_notice'] = (
                        'Tus grupos han cambiado. Los tokens anteriores han sido invalidados. '
                        'Por favor, inicia sesión nuevamente.'
                    )
            
            except ImportError:
                logger.warning(
                    "⚠️ No se pudo invalidar tokens: token_blacklist no está instalado"
                )
            except Exception as e:
                logger.error(f"❌ Error al invalidar tokens del usuario {instance.run}: {e}")
        
        return response


# ============================================================
# CATALOGS ViewSets
# ============================================================

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
            return 'catalogs.change_catnacionalidad'
        return 'catalogs.view_catnacionalidad'
    
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
            # 1. Crear: Pide 'add'
            if self.action == 'create':
                return 'catalogs.add_catpueblooriginario'
                
            # 2. Editar: Pide 'change'
            elif self.action in ['update', 'partial_update']:
                return 'catalogs.change_catpueblooriginario'
                
            # 3. Borrar: Pide 'delete' (Aquí cierras la fuga de seguridad)
            elif self.action == 'destroy':
                return 'catalogs.delete_catpueblooriginario'
                
            # 4. Ver: Pide 'view'
            return 'catalogs.view_catpueblooriginario'
    
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
        # 1. Crear: Pide 'add'
        if self.action == 'create':
            return 'catalogs.add_catcomplicacionparto'
            
        # 2. Editar: Pide 'change'
        elif self.action in ['update', 'partial_update']:
            return 'catalogs.change_catcomplicacionparto'
            
        # 3. Borrar: Pide 'delete' (Cierra la fuga de seguridad)
        elif self.action == 'destroy':
            return 'catalogs.delete_catcomplicacionparto'
            
        # 4. Ver: Pide 'view'
        return 'catalogs.view_catcomplicacionparto'
    
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
        # 1. Crear: Pide 'add'
        if self.action == 'create':
            return 'catalogs.add_catrobson'
            
        # 2. Editar: Pide 'change'
        elif self.action in ['update', 'partial_update']:
            return 'catalogs.change_catrobson'
            
        # 3. Borrar: Pide 'delete' (Corrige la vulnerabilidad)
        elif self.action == 'destroy':
            return 'catalogs.delete_catrobson'
            
        # 4. Ver: Pide 'view'
        return 'catalogs.view_catrobson'
    
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
        # 1. Crear: Pide 'add'
        if self.action == 'create':
            return 'catalogs.add_cattipoparto'
            
        # 2. Editar: Pide 'change'
        elif self.action in ['update', 'partial_update']:
            return 'catalogs.change_cattipoparto'
            
        # 3. Borrar: Pide 'delete' (Corrige la vulnerabilidad)
        elif self.action == 'destroy':
            return 'catalogs.delete_cattipoparto'
            
        # 4. Ver: Pide 'view'
        return 'catalogs.view_cattipoparto'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)

# ============================================================
# MATERNITY ViewSets
# ============================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Maternidad'], 
        summary='Listar madres pacientes',
        description='Retorna lista paginada de madres. Requiere: maternity.view_madrepaciente',
        parameters=[
            OpenApiParameter('run', str, description='Filtrar por RUN'),
            OpenApiParameter('fk_nacionalidad', int, description='Filtrar por nacionalidad'),
        ]
    ),
    create=extend_schema(tags=['Maternidad'], summary='Crear madre paciente', description='Requiere: maternity.add_madrepaciente'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener madre paciente'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar madre paciente'),
    partial_update=extend_schema(tags=['Maternidad'], summary='Actualizar madre (parcial)'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar madre paciente'),
)
class MadrePacienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de madres pacientes con permisos nativos."""
    queryset = MadrePaciente.objects.all()
    serializer_class = MadrePacienteSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    search_fields = ['run', 'nombre', 'apellido_paterno', 'apellido_materno']
    filterset_fields = ['fk_nacionalidad', 'fk_pueblo_originario']
    
    def get_required_permission(self):
        # 1. Acciones Estándar
        if self.action == 'create':
            return 'maternity.add_madrepaciente'
        elif self.action in ['update', 'partial_update']:
            return 'maternity.change_madrepaciente'
        elif self.action == 'destroy':
            return 'maternity.delete_madrepaciente'
            
        # 2. 🔴 Acciones Personalizadas (Sub-recursos) - Validación Estricta 🔴
        elif self.action == 'embarazos':
            return 'maternity.view_embarazo' # Exige permiso de ver embarazo
            
        elif self.action == 'partos':
            return 'maternity.view_parto'    # Exige permiso de ver parto
            
        elif self.action == 'ive_atenciones':
            return 'maternity.view_iveatencion' # Exige permiso de ver IVE
            
        # 3. Por defecto (Ver Madre)
        return 'maternity.view_madrepaciente'
    
    def check_permissions(self, request):
        # Limpiamos esto para confiar en la lógica centralizada de arriba
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
    """ViewSet para gestión de embarazos con permisos nativos."""
    queryset = Embarazo.objects.all()
    serializer_class = EmbarazoSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_madre']
    ordering_fields = ['semana_obstetrica', 'fecha_registro']
    
    def get_required_permission(self):
            if self.action == 'create':
                return 'maternity.add_embarazo'
            
            # Bloque solo para editar
            elif self.action in ['update', 'partial_update']:
                return 'maternity.change_embarazo'
                
            # Bloque exclusivo para borrar
            elif self.action == 'destroy':
                return 'maternity.delete_embarazo' # <--- Ahora sí exige el permiso de borrar
                
            return 'maternity.view_embarazo'
    
    def check_permissions(self, request):
        if self.action == 'detalle':
            self.required_permission = 'maternity.view_embarazo'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    def validar_permiso_objeto(self, usuario, obj):
        """Validación a nivel de objeto para Matronas con restricción de turno."""
        return puede_modificar_registro_turno(usuario, obj)
    
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
        description='Requiere: maternity.view_parto. Matronas con restricción de turno.',
        parameters=[
            OpenApiParameter('fk_madre', int, description='Filtrar por madre'),
            OpenApiParameter('fk_tipo_parto', int, description='Filtrar por tipo de parto'),
        ]
    ),
    create=extend_schema(tags=['Maternidad'], summary='Crear parto', description='Requiere: maternity.add_parto'),
    retrieve=extend_schema(tags=['Maternidad'], summary='Obtener parto (detalle completo)'),
    update=extend_schema(tags=['Maternidad'], summary='Actualizar parto'),
    destroy=extend_schema(tags=['Maternidad'], summary='Eliminar parto'),
)
class PartoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de partos con permisos nativos y restricción de turno."""
    queryset = Parto.objects.all()
    serializer_class = PartoDetailSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_madre', 'fk_tipo_parto']
    ordering_fields = ['fecha_parto', 'fecha_registro']
    
    def get_required_permission(self):
        # 1. Creación
        if self.action == 'create':
            return 'maternity.add_parto'
        
        # 2. Edición
        elif self.action in ['update', 'partial_update']:
            return 'maternity.change_parto'
        
        # 3. Eliminación
        elif self.action == 'destroy':
            return 'maternity.delete_parto'

        # 4. 🔴 NUEVO: Validación estricta para sub-recursos 🔴
        # Si piden complicaciones, exigimos el permiso de complicaciones
        elif self.action == 'complicaciones':
            return 'maternity.view_partocomplicacion'
        
        # Si piden anestesias, exigimos el permiso de anestesias
        elif self.action == 'anestesias':
            return 'maternity.view_partoanestesia'
            
        # 5. Por defecto (Listar/Ver Parto general)
        return 'maternity.view_parto'
    
    def check_permissions(self, request):
        # 🔴 CORREGIDO: Eliminamos el 'if' manual que causaba la fuga.
        # Ahora confiamos 100% en la lógica de get_required_permission.
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)

    def validar_permiso_objeto(self, usuario, obj):
        """Validación de restricción de turno para Matronas."""
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
    """ViewSet para gestión de complicaciones de parto con permisos nativos."""
    queryset = PartoComplicacion.objects.all()
    serializer_class = PartoComplicacionSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_parto', 'fk_complicacion']
    
    def get_required_permission(self):
            # 1. Crear: Pide explícitamente 'add'
            if self.action == 'create':
                return 'maternity.add_partocomplicacion'
                
            # 2. Editar: Pide 'change'
            elif self.action in ['update', 'partial_update']:
                return 'maternity.change_partocomplicacion'
                
            # 3. Borrar: Pide 'delete' (Aquí cierras la última puerta trasera)
            elif self.action == 'destroy':
                return 'maternity.delete_partocomplicacion'
                
            # 4. Ver (y acción 'por_parto'): Pide 'view'
            return 'maternity.view_partocomplicacion'
    
    def check_permissions(self, request):
        if self.action == 'por_parto':
            self.required_permission = 'maternity.view_partocomplicacion'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    def validar_permiso_objeto(self, usuario, obj):
        """Las Matronas solo pueden modificar complicaciones de partos de su turno."""
        return puede_modificar_registro_turno(usuario, obj.fk_parto)
    
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
    """ViewSet para gestión de anestesias de parto con permisos nativos."""
    queryset = PartoAnestesia.objects.all()
    serializer_class = PartoAnestesiaSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_parto', 'tipo_anestesia']
    
    def get_required_permission(self):
            # 1. Crear: Pide explícitamente 'add'
            if self.action == 'create':
                return 'maternity.add_partoanestesia'
                
            # 2. Editar: Pide 'change'
            elif self.action in ['update', 'partial_update']:
                return 'maternity.change_partoanestesia'
                
            # 3. Borrar: Pide 'delete' (Seguridad crítica)
            elif self.action == 'destroy':
                return 'maternity.delete_partoanestesia'
                
            # 4. Ver (y estadísticas): Pide 'view'
            return 'maternity.view_partoanestesia'
    
    def check_permissions(self, request):
        if self.action == 'estadisticas':
            self.required_permission = 'maternity.view_partoanestesia'
        else:
            self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    def validar_permiso_objeto(self, usuario, obj):
        """Las Matronas solo pueden modificar anestesias de partos de su turno."""
        return puede_modificar_registro_turno(usuario, obj.fk_parto)
    
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
    """ViewSet para gestión de atenciones IVE con permisos nativos."""
    queryset = IVEAtencion.objects.all()
    serializer_class = IVEAtencionDetailSerializer
    permission_classes = [IsAuthenticated, RBACPermission, RBACObjectPermission]
    filterset_fields = ['fk_madre', 'fk_causal']
    ordering_fields = ['fecha_atencion']
    
    def get_required_permission(self):
        # 1. Crear: Pide 'add'
        if self.action == 'create':
            return 'maternity.add_iveatencion'
            
        # 2. Editar: Pide 'change'
        elif self.action in ['update', 'partial_update']:
            return 'maternity.change_iveatencion'
            
        # 3. Borrar: Pide 'delete' (Cierra la fuga de seguridad)
        elif self.action == 'destroy':
            return 'maternity.delete_iveatencion'
            
        # 4. Sub-recurso: Exigimos permiso específico de acompañamiento
        elif self.action == 'acompaniamientos':
            return 'maternity.view_iveacompanamiento'
            
        # 5. Ver: Pide 'view'
        return 'maternity.view_iveatencion'
    
    def check_permissions(self, request):
        # Limpiamos para confiar en la lógica centralizada
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)
    
    def validar_permiso_objeto(self, usuario, obj):
        """Las Matronas solo pueden modificar atenciones IVE de su turno."""
        return puede_modificar_registro_turno(usuario, obj)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IVEAtencionDetailSerializer
        return IVEAtencionSerializer
    
    @extend_schema(tags=['Maternidad'], summary='Obtener acompañamientos de una atención IVE')
    @action(detail=True, methods=['get'])
    def acompaniamientos(self, request, pk=None):
        ive = self.get_object()
        # Nota: Asegúrate de que el related_name en tu modelo sea 'acompañamientos' o 'ive_acompanamientos'
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
    """ViewSet para gestión de acompañamientos IVE con permisos nativos."""
    queryset = IVEAcompanamiento.objects.all()
    serializer_class = IVEAcompanamientoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['fk_ive_atencion', 'tipo_profesional']
    
    def get_required_permission(self):
        # 1. Crear: Pide 'add'
        if self.action == 'create':
            return 'maternity.add_iveacompanamiento'
            
        # 2. Editar: Pide 'change'
        elif self.action in ['update', 'partial_update']:
            return 'maternity.change_iveacompanamiento'
            
        # 3. Borrar: Pide 'delete' (Seguridad crítica)
        elif self.action == 'destroy':
            return 'maternity.delete_iveacompanamiento'
            
        # 4. Ver (Retrieve, List y tipos_disponibles): Pide 'view'
        return 'maternity.view_iveacompanamiento'
    
    def check_permissions(self, request):
        # Lógica centralizada y limpia
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
    """ViewSet para gestión de altas anticonceptivas con permisos nativos."""
    queryset = AltaAnticonceptivo.objects.all()
    serializer_class = AltaAnticonceptivoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    filterset_fields = ['tipo_alta', 'esterilizacion_quirurgica']
    ordering_fields = ['fecha_registro']
    
    def get_required_permission(self):
            # 1. Crear: Pide permiso 'add'
            if self.action == 'create':
                return 'maternity.add_altaanticonceptivo'
                
            # 2. Editar: Pide permiso 'change'
            elif self.action in ['update', 'partial_update']:
                return 'maternity.change_altaanticonceptivo'
                
            # 3. Borrar: Pide permiso 'delete' (Esto soluciona el 404 -> 403)
            elif self.action == 'destroy':
                return 'maternity.delete_altaanticonceptivo'
                
            # 4. Ver: Pide permiso 'view'
            return 'maternity.view_altaanticonceptivo'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============================================================
# NEONATOLOGY ViewSets
# ============================================================

@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar recién nacidos'),
    create=extend_schema(tags=['Neonatología'], summary='Crear recién nacido', description='Requiere: neonatology.add_reciennacido'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener recién nacido'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar recién nacido'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar recién nacido'),
)
class RecienNacidoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de recién nacidos con permisos nativos."""
    queryset = RecienNacido.objects.all()
    serializer_class = RecienNacidoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
            if self.action == 'create':
                return 'neonatology.add_reciennacido'
            
            # ✅ CORRECCIÓN: Solo update y partial_update piden 'change'
            elif self.action in ['update', 'partial_update']:
                return 'neonatology.change_reciennacido'
                
            # ✅ NUEVO BLOQUE: destroy pide explícitamente 'delete'
            elif self.action == 'destroy':
                return 'neonatology.delete_reciennacido'
            
            return 'neonatology.view_reciennacido'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar atenciones inmediatas RN'),
    create=extend_schema(tags=['Neonatología'], summary='Crear atención inmediata RN', description='Requiere: neonatology.add_rnatencioninmediata'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener atención inmediata RN'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar atención inmediata RN'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar atención inmediata RN'),
)
class RNAtencionInmediataViewSet(viewsets.ModelViewSet):
    """ViewSet para atención inmediata de RN con permisos nativos."""
    queryset = RNAtencionInmediata.objects.all()
    serializer_class = RNAtencionInmediataSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
            # 1. Crear: Pide explícitamente 'add'
            if self.action == 'create':
                return 'neonatology.add_rnatencioninmediata'
                
            # 2. Editar: Pide 'change'
            elif self.action in ['update', 'partial_update']:
                return 'neonatology.change_rnatencioninmediata'
                
            # 3. Borrar: Pide 'delete' (Aquí cierras la brecha de seguridad)
            elif self.action == 'destroy':
                return 'neonatology.delete_rnatencioninmediata'
                
            # 4. Ver: Pide 'view'
            return 'neonatology.view_rnatencioninmediata'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar tamizajes metabólicos'),
    create=extend_schema(tags=['Neonatología'], summary='Crear tamizaje metabólico', description='Requiere: neonatology.add_rntamizajemetabolico'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener tamizaje metabólico'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar tamizaje metabólico'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar tamizaje metabólico'),
)
class RNTamizajeMetabolicoViewSet(viewsets.ModelViewSet):
    """ViewSet para tamizaje metabólico de RN con permisos nativos."""
    queryset = RNTamizajeMetabolico.objects.all()
    serializer_class = RNTamizajeMetabolicoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
            # 1. Para crear, pedimos 'add'
            if self.action == 'create':
                return 'neonatology.add_rntamizajemetabolico'
                
            # 2. Para editar, pedimos 'change'
            elif self.action in ['update', 'partial_update']:
                return 'neonatology.change_rntamizajemetabolico'
                
            # 3. Para borrar, pedimos 'delete' (¡AQUÍ ESTÁ LA SOLUCIÓN!)
            elif self.action == 'destroy':
                return 'neonatology.delete_rntamizajemetabolico'
                
            # 4. Para todo lo demás (listar/ver), pedimos 'view'
            return 'neonatology.view_rntamizajemetabolico'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar tamizajes auditivos'),
    create=extend_schema(tags=['Neonatología'], summary='Crear tamizaje auditivo', description='Requiere: neonatology.add_rntamizajeauditivo'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener tamizaje auditivo'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar tamizaje auditivo'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar tamizaje auditivo'),
)
class RNTamizajeAuditivoViewSet(viewsets.ModelViewSet):
    """ViewSet para tamizaje auditivo de RN con permisos nativos."""
    queryset = RNTamizajeAuditivo.objects.all()
    serializer_class = RNTamizajeAuditivoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
        
    def get_required_permission(self):
            # 1. Crear: Pide permiso 'add'
            if self.action == 'create':
                return 'neonatology.add_rntamizajeauditivo'
                
            # 2. Editar: Pide permiso 'change'
            elif self.action in ['update', 'partial_update']:
                return 'neonatology.change_rntamizajeauditivo'
                
            # 3. Borrar: Pide permiso 'delete' (Esto soluciona el 404 -> 403)
            elif self.action == 'destroy':
                return 'neonatology.delete_rntamizajeauditivo'
                
            # 4. Ver: Pide permiso 'view'
            return 'neonatology.view_rntamizajeauditivo'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar tamizajes de cardiopatías'),
    create=extend_schema(tags=['Neonatología'], summary='Crear tamizaje de cardiopatía', description='Requiere: neonatology.add_rntamizajecardiopatia'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener tamizaje de cardiopatía'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar tamizaje de cardiopatía'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar tamizaje de cardiopatía'),
)
class RNTamizajeCardiopatiaViewSet(viewsets.ModelViewSet):
    """ViewSet para tamizaje de cardiopatías de RN con permisos nativos."""
    queryset = RNTamizajeCardiopatia.objects.all()
    serializer_class = RNTamizajeCardiopatiaSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
            # 1. Crear: Pide permiso 'add'
            if self.action == 'create':
                return 'neonatology.add_rntamizajecardiopatia'
                
            # 2. Editar: Pide permiso 'change'
            elif self.action in ['update', 'partial_update']:
                return 'neonatology.change_rntamizajecardiopatia'
                
            # 3. Borrar: Pide permiso 'delete' (Corrige la fuga de seguridad)
            elif self.action == 'destroy':
                return 'neonatology.delete_rntamizajecardiopatia'
                
            # 4. Ver: Pide permiso 'view'
            return 'neonatology.view_rntamizajecardiopatia'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


@extend_schema_view(
    list=extend_schema(tags=['Neonatología'], summary='Listar egresos de RN'),
    create=extend_schema(tags=['Neonatología'], summary='Crear egreso de RN', description='Requiere: neonatology.add_rnegreso'),
    retrieve=extend_schema(tags=['Neonatología'], summary='Obtener egreso de RN'),
    update=extend_schema(tags=['Neonatología'], summary='Actualizar egreso de RN'),
    destroy=extend_schema(tags=['Neonatología'], summary='Eliminar egreso de RN'),
)
class RNEgresoViewSet(viewsets.ModelViewSet):
    """ViewSet para egreso de RN con permisos nativos."""
    queryset = RNEgreso.objects.all()
    serializer_class = RNEgresoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
            # 1. Crear: Pide permiso 'add'
            if self.action == 'create':
                return 'neonatology.add_rnegreso'
                
            # 2. Editar: Pide permiso 'change'
            elif self.action in ['update', 'partial_update']:
                return 'neonatology.change_rnegreso'
                
            # 3. Borrar: Pide permiso 'delete' (Corrige la fuga de seguridad)
            elif self.action == 'destroy':
                return 'neonatology.delete_rnegreso'
                
            # 4. Ver: Pide permiso 'view'
            return 'neonatology.view_rnegreso'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============================================================
# COMPLIANCE ViewSets
# ============================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Auditoría'], 
        summary='Listar trazas de auditoría', 
        description='Solo lectura. Requiere: compliance.view_trazamovimiento (solo supervisores)',
        parameters=[
            OpenApiParameter('tipo_accion', str, description='Filtrar por tipo de acción'),
            OpenApiParameter('tabla_afectada', str, description='Filtrar por tabla afectada'),
        ]
    ),
    retrieve=extend_schema(tags=['Auditoría'], summary='Obtener traza de auditoría'),
)
class TrazaMovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para auditoría con permisos nativos."""
    queryset = TrazaMovimiento.objects.all()
    serializer_class = TrazaMovimientoSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'compliance.view_trazamovimiento'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============================================================
# ALERTS ViewSets
# ============================================================

@extend_schema_view(
    list=extend_schema(tags=['Alertas'], summary='Listar alertas del sistema', description='Requiere: alerts.view_alertasistema'),
    create=extend_schema(tags=['Alertas'], summary='Crear alerta', description='Requiere: alerts.add_alertasistema'),
    retrieve=extend_schema(tags=['Alertas'], summary='Obtener alerta'),
    update=extend_schema(tags=['Alertas'], summary='Actualizar alerta (resolver)', description='Requiere: alerts.change_alertasistema'),
    partial_update=extend_schema(tags=['Alertas'], summary='Actualizar alerta parcialmente'),
    destroy=extend_schema(tags=['Alertas'], summary='Eliminar alerta', description='Requiere: alerts.delete_alertasistema'),
)
class AlertaSistemaViewSet(viewsets.ModelViewSet):
    """ViewSet para alertas del sistema con permisos nativos."""
    queryset = AlertaSistema.objects.all()
    serializer_class = AlertaSistemaSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        if self.action in ['update', 'partial_update']:
            return 'alerts.change_alertasistema'
        elif self.action == 'create':
            return 'alerts.add_alertasistema'
        elif self.action == 'destroy':
            return 'alerts.delete_alertasistema'
        return 'alerts.view_alertasistema'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)


# ============================================================
# REPORTS ViewSets
# ============================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Reportes'], 
        summary='Listar reportes REM', 
        description='Requiere: reports.view_reporterem'
    ),
    create=extend_schema(tags=['Reportes'], summary='Generar reporte REM', description='Requiere: reports.add_reporterem'),
    retrieve=extend_schema(tags=['Reportes'], summary='Obtener reporte REM'),
    update=extend_schema(tags=['Reportes'], summary='Actualizar reporte REM'),
    destroy=extend_schema(tags=['Reportes'], summary='Eliminar reporte REM'),
)
class ReporteREMViewSet(viewsets.ModelViewSet):
    """ViewSet para reportes REM con permisos nativos."""
    queryset = ReporteREM.objects.all()
    serializer_class = ReporteREMSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        # 1. Crear: Pide 'add'
        if self.action == 'create':
            return 'reports.add_reporterem'
            
        # 2. Editar: Pide 'change'
        elif self.action in ['update', 'partial_update']:
            return 'reports.change_reporterem'
            
        # 3. Borrar: Pide 'delete' (Aquí cierras la puerta trasera)
        elif self.action == 'destroy':
            return 'reports.delete_reporterem'
            
        # 4. Ver: Pide 'view'
        return 'reports.view_reporterem'
    
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
    """ViewSet para detalles de reportes REM con permisos nativos."""
    queryset = ReporteREMDetalle.objects.all()
    serializer_class = ReporteREMDetalleSerializer
    permission_classes = [IsAuthenticated, RBACPermission]
    
    def get_required_permission(self):
        return 'reports.view_reporteremdetalle'
    
    def check_permissions(self, request):
        self.required_permission = self.get_required_permission()
        super().check_permissions(request)