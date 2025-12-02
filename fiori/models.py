"""
Modelos para el Sistema Fiori Launchpad
Integrado con Django Groups (Roles) nativos
"""
from django.db import models
from django.contrib.auth.models import Group
from core.models import Usuario
from django.core.validators import MinValueValidator, MaxValueValidator


class FioriAppCategory(models.Model):
    """Categorías para organizar las aplicaciones Fiori."""
    id_category = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, help_text="Nombre de la categoría")
    description = models.TextField(blank=True, help_text="Descripción de la categoría")
    icon = models.CharField(max_length=50, default='folder', help_text="Icono UI5 (ej: 'folder', 'group')")
    order = models.IntegerField(default=0, help_text="Orden de visualización")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fiori_app_category'
        verbose_name = 'Categoría de Aplicación Fiori'
        verbose_name_plural = 'Categorías de Aplicaciones Fiori'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class FioriApp(models.Model):
    """
    Definición de cada aplicación Fiori disponible en el sistema.
    Similar a las Tiles del SAP Fiori Launchpad real.
    """
    TILE_TYPE_CHOICES = [
        ('standard', 'Standard Tile'),
        ('feed', 'Feed Tile'),
        ('numeric', 'Numeric Content'),
        ('link', 'Link Tile'),
    ]
    
    TILE_SIZE_CHOICES = [
        ('1x1', '1x1'),
        ('1x2', '1x2'),
        ('2x2', '2x2'),
    ]
    
    id_app = models.AutoField(primary_key=True)
    
    # Identificación
    app_id = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="ID único de la app (ej: 'madres-list', 'partos-create')"
    )
    title = models.CharField(max_length=100, help_text="Título de la aplicación")
    subtitle = models.CharField(max_length=200, blank=True, help_text="Subtítulo descriptivo")
    description = models.TextField(blank=True, help_text="Descripción completa de la app")
    
    
    # Visualización
    icon = models.CharField(
        max_length=50, 
        default='activity-items',
        help_text="Icono SAP UI5 (ej: 'patient', 'clinical-order', 'doctor')"
    )
    tile_type = models.CharField(
        max_length=20, 
        choices=TILE_TYPE_CHOICES, 
        default='standard',
        help_text="Tipo de tile"
    )
    tile_size = models.CharField(
        max_length=5, 
        choices=TILE_SIZE_CHOICES, 
        default='1x1',
        help_text="Tamaño del tile"
    )
    background_color = models.CharField(
        max_length=20, 
        default='Accent6',
        help_text="Color de fondo SAP (ej: 'Accent1', 'Accent6', 'Neutral')"
    )
    
    # Navegación
    url_path = models.CharField(
        max_length=200, 
        help_text="Ruta URL de la app (ej: '/fiori/madres/list/')"
    )
    module_name = models.CharField(
        max_length=100,
        help_text="Nombre del módulo Python (ej: 'fiori.madres')"
    )
    
    # Control de Acceso
    required_permissions = models.JSONField(
        default=list,
        help_text="Lista de permisos requeridos ['app.perm1', 'app.perm2']",
        blank=True
    )
    allowed_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='fiori_apps',
        help_text="Grupos (roles) que pueden acceder"
    )
    
    # Categorización
    category = models.ForeignKey(
        FioriAppCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apps',
        help_text="Categoría de la aplicación"
    )
    
    # Metadata
    is_transactional = models.BooleanField(
        default=True,
        help_text="¿Es una app transaccional o analítica?"
    )
    is_mobile_ready = models.BooleanField(
        default=True,
        help_text="¿Está optimizada para móviles?"
    )
    default_order = models.IntegerField(
        default=0,
        help_text="Orden predeterminado en el FLP"
    )
    active = models.BooleanField(
        default=True,
        help_text="¿Está activa la aplicación?"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_fiori_apps'
    )
    
    class Meta:
        db_table = 'fiori_app'
        verbose_name = 'Aplicación Fiori'
        verbose_name_plural = 'Aplicaciones Fiori'
        ordering = ['default_order', 'title']
        indexes = [
            models.Index(fields=['app_id']),
            models.Index(fields=['active', 'default_order']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.app_id})"
    
    def is_accessible_by_user(self, user):
        """Verifica si un usuario puede acceder a esta app."""
        if not self.active:
            return False
        
        if user.is_superuser:
            return True
        
        # Verificar grupos
        if self.allowed_groups.exists():
            user_groups = set(user.groups.all())
            allowed_groups = set(self.allowed_groups.all())
            if not user_groups.intersection(allowed_groups):
                return False
        
        # Verificar permisos
        if self.required_permissions:
            for perm in self.required_permissions:
                if not user.has_perm(perm):
                    return False
        
        return True


class UserAppConfig(models.Model):
    """
    Configuración personalizada de aplicaciones por usuario.
    Permite al usuario organizar sus propias apps en el FLP.
    """
    id_config = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='app_configs',
        db_column='fk_usuario'
    )
    app = models.ForeignKey(
        FioriApp,
        on_delete=models.CASCADE,
        related_name='user_configs',
        db_column='fk_app'
    )
    
    # Personalización
    is_visible = models.BooleanField(
        default=True,
        help_text="¿Está visible en el FLP del usuario?"
    )
    custom_order = models.IntegerField(
        default=0,
        help_text="Orden personalizado por el usuario"
    )
    is_favorite = models.BooleanField(
        default=False,
        help_text="¿Está marcada como favorita?"
    )
    custom_group_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre de grupo personalizado (opcional)"
    )
    
    # Estadísticas de uso
    access_count = models.IntegerField(
        default=0,
        help_text="Cantidad de veces que accedió"
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que accedió"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_app_config'
        verbose_name = 'Configuración de App por Usuario'
        verbose_name_plural = 'Configuraciones de Apps por Usuario'
        unique_together = ('user', 'app')
        ordering = ['custom_order', 'app__title']
        indexes = [
            models.Index(fields=['user', 'is_visible']),
            models.Index(fields=['user', 'custom_order']),
        ]
    
    def __str__(self):
        return f"{self.user.nombre_completo} - {self.app.title}"
    
    def increment_access(self):
        """Incrementa el contador de accesos."""
        from django.utils import timezone
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])


class FioriGroup(models.Model):
    """
    Grupos de aplicaciones en el FLP.
    Permite organizar apps en secciones como "Maternidad", "Neonatología", etc.
    """
    id_group = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, help_text="Nombre del grupo")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='group', help_text="Icono del grupo")
    order = models.IntegerField(default=0, help_text="Orden de visualización")
    is_active = models.BooleanField(
        default=True,
        help_text="¿Está activo el grupo?"
    )
    is_collapsible = models.BooleanField(
        default=True,
        help_text="¿Se puede colapsar el grupo?"
    )
    collapsed_by_default = models.BooleanField(
        default=False,
        help_text="¿Está colapsado por defecto?"
    )
    apps = models.ManyToManyField(
        FioriApp,
        through='FioriGroupApp',
        related_name='groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fiori_group'
        verbose_name = 'Grupo de Aplicaciones Fiori'
        verbose_name_plural = 'Grupos de Aplicaciones Fiori'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class FioriGroupApp(models.Model):
    """Relación entre grupos y aplicaciones con orden."""
    group = models.ForeignKey(FioriGroup, on_delete=models.CASCADE)
    app = models.ForeignKey(FioriApp, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'fiori_group_app'
        unique_together = ('group', 'app')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.group.name} - {self.app.title}"


class UserFioriPreferences(models.Model):
    """
    Preferencias globales del usuario para el FLP.
    """
    user = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='fiori_preferences',
        db_column='fk_usuario'
    )
    
    # Preferencias de Visualización
    theme = models.CharField(
        max_length=20,
        default='sap_horizon',
        choices=[
            ('sap_horizon', 'SAP Horizon'),
            ('sap_fiori_3', 'SAP Fiori 3'),
            ('sap_belize', 'SAP Belize'),
        ],
        help_text="Tema visual del FLP"
    )
    tile_size_preference = models.CharField(
        max_length=5,
        default='1x1',
        choices=FioriApp.TILE_SIZE_CHOICES,
        help_text="Tamaño preferido de tiles"
    )
    compact_mode = models.BooleanField(
        default=False,
        help_text="Modo compacto (más tiles por fila)"
    )
    
    # Preferencias de Organización
    group_by_category = models.BooleanField(
        default=True,
        help_text="Agrupar apps por categoría"
    )
    show_recent_apps = models.BooleanField(
        default=True,
        help_text="Mostrar sección de apps recientes"
    )
    recent_apps_count = models.IntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(10)],
        help_text="Cantidad de apps recientes a mostrar"
    )
    
    # Preferencias de Notificaciones
    enable_notifications = models.BooleanField(
        default=True,
        help_text="Habilitar notificaciones"
    )
    notification_sound = models.BooleanField(
        default=False,
        help_text="Sonido en notificaciones"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_fiori_preferences'
        verbose_name = 'Preferencias Fiori del Usuario'
        verbose_name_plural = 'Preferencias Fiori de Usuarios'
    
    def __str__(self):
        return f"Preferencias de {self.user.nombre_completo}"
    
class LaunchpadSettings(models.Model):
    """Configuraciones del Launchpad por usuario"""
    user = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='launchpad_settings',
        db_column='fk_usuario'
    )
    
    theme = models.CharField(
        max_length=20,
        default='sap_fiori_3',
        choices=[
            ('sap_fiori_3', 'SAP Fiori 3'),
            ('sap_horizon', 'SAP Horizon'),
            ('sap_belize', 'SAP Belize'),
        ],
        help_text="Tema visual del Launchpad"
    )
    view_mode = models.CharField(
        max_length=20,
        default='comfortable',
        choices=[
            ('comfortable', 'Comfortable'),
            ('cozy', 'Cozy'),
            ('compact', 'Compact'),
        ],
        help_text="Modo de vista del Launchpad"
    )
    show_groups = models.BooleanField(
        default=True,
        help_text="¿Mostrar grupos de aplicaciones?"
    )
    tiles_per_row = models.IntegerField(
        default=4,
        validators=[MinValueValidator(2), MaxValueValidator(6)],
        help_text="Cantidad de tiles por fila"
    )
    default_app = models.ForeignKey(
        FioriApp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_users',
        help_text="Aplicación predeterminada al iniciar sesión"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'launchpad_settings'
        verbose_name = 'Configuración del Launchpad'
        verbose_name_plural = 'Configuraciones del Launchpad'
    
    def __str__(self):
        return f"Launchpad Settings for {self.user.nombre_completo}"