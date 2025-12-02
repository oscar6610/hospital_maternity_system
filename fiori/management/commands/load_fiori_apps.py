"""
Comando de Django Management para cargar aplicaciones Fiori iniciales.

Uso:
    python manage.py load_fiori_apps
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from fiori.models import FioriApp, FioriAppCategory


class Command(BaseCommand):
    help = 'Carga las aplicaciones Fiori iniciales del sistema Hospital Maternity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de aplicaciones Fiori...'))
        
        # Crear categorías
        self.stdout.write('Creando categorías...')
        categories = self.create_categories()
        
        # Crear aplicaciones
        self.stdout.write('Creando aplicaciones...')
        apps_created = self.create_apps(categories)
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Carga completada exitosamente!'
            f'\n   - {len(categories)} categorías creadas'
            f'\n   - {apps_created} aplicaciones creadas'
        ))
    
    def create_categories(self):
        """Crear categorías de aplicaciones."""
        categories_data = [
            {
                'name': 'Maternidad',
                'description': 'Aplicaciones para la gestión de maternidad y partos',
                'icon': 'clinical-order',
                'order': 1
            },
            {
                'name': 'Neonatología',
                'description': 'Aplicaciones para la gestión de recién nacidos',
                'icon': 'baby-care',
                'order': 2
            },
            {
                'name': 'Reportes',
                'description': 'Generación y consulta de reportes estadísticos',
                'icon': 'business-objects-experience',
                'order': 3
            },
            {
                'name': 'Administración',
                'description': 'Herramientas de administración del sistema',
                'icon': 'settings',
                'order': 4
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = FioriAppCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            
            if created:
                self.stdout.write(f'  ✓ Categoría creada: {category.name}')
            else:
                self.stdout.write(f'  • Categoría existente: {category.name}')
        
        return categories
    
    def create_apps(self, categories):
        """Crear aplicaciones Fiori."""
        
        # Obtener grupos (roles)
        try:
            matrona = Group.objects.get(name='Matrona Clínica')
            supervisor = Group.objects.get(name='Supervisor/Jefe de Área')
            medico = Group.objects.get(name='Médico(a)')
            enfermero = Group.objects.get(name='Enfermero(a)')
            administrativo = Group.objects.get(name='Administrativo(a)')
        except Group.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Error: Rol no encontrado - {e}'))
            return 0
        
        apps_data = [
            # ========== MATERNIDAD ==========
            {
                'app_id': 'madres-list',
                'title': 'Gestión de Madres',
                'subtitle': 'Registro y seguimiento de madres pacientes',
                'description': 'Aplicación para gestionar el registro completo de madres pacientes, incluyendo datos demográficos, embarazos y partos.',
                'icon': 'patient',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent1',
                'url_path': '/fiori/madres/list/',
                'module_name': 'fiori.madres',
                'category': categories['Maternidad'],
                'required_permissions': ['maternity.view_madrepaciente'],
                'allowed_groups': [matrona, supervisor, medico, administrativo],
                'is_transactional': True,
                'default_order': 1
            },
            {
                'app_id': 'madres-create',
                'title': 'Registrar Madre',
                'subtitle': 'Ingreso de nueva madre paciente',
                'description': 'Formulario de registro rápido para ingresar nuevas madres al sistema.',
                'icon': 'add',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent2',
                'url_path': '/fiori/madres/create/',
                'module_name': 'fiori.madres',
                'category': categories['Maternidad'],
                'required_permissions': ['maternity.add_madrepaciente'],
                'allowed_groups': [matrona, supervisor, administrativo],
                'is_transactional': True,
                'default_order': 2
            },
            {
                'app_id': 'embarazos-list',
                'title': 'Gestión de Embarazos',
                'subtitle': 'Control de embarazos y seguimiento',
                'description': 'Seguimiento de embarazos, control prenatal y cálculo de semanas obstétricas.',
                'icon': 'doctor',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent3',
                'url_path': '/fiori/madres/embarazos/',
                'module_name': 'fiori.madres',
                'category': categories['Maternidad'],
                'required_permissions': ['maternity.view_embarazo'],
                'allowed_groups': [matrona, supervisor, medico],
                'is_transactional': True,
                'default_order': 3
            },
            {
                'app_id': 'partos-list',
                'title': 'Gestión de Partos',
                'subtitle': 'Registro y seguimiento de partos',
                'description': 'Aplicación completa para gestionar partos, complicaciones, anestesias y clasificación Robson.',
                'icon': 'clinical-tast-tracker',
                'tile_type': 'standard',
                'tile_size': '1x2',
                'background_color': 'Accent4',
                'url_path': '/fiori/partos/list/',
                'module_name': 'fiori.partos',
                'category': categories['Maternidad'],
                'required_permissions': ['maternity.view_parto'],
                'allowed_groups': [matrona, supervisor, medico],
                'is_transactional': True,
                'default_order': 4
            },
            {
                'app_id': 'ive-atenciones',
                'title': 'Atenciones IVE',
                'subtitle': 'Interrupción Voluntaria del Embarazo',
                'description': 'Gestión de atenciones IVE según las tres causales legales, incluyendo acompañamientos profesionales.',
                'icon': 'stethoscope',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent5',
                'url_path': '/fiori/madres/ive/',
                'module_name': 'fiori.madres',
                'category': categories['Maternidad'],
                'required_permissions': ['maternity.view_iveatencion'],
                'allowed_groups': [matrona, supervisor, medico],
                'is_transactional': True,
                'default_order': 5
            },
            
            # ========== NEONATOLOGÍA ==========
            {
                'app_id': 'rn-list',
                'title': 'Gestión de Recién Nacidos',
                'subtitle': 'Registro de RN y atención inmediata',
                'description': 'Gestión completa de recién nacidos, incluyendo datos antropométricos, APGAR y profilaxis.',
                'icon': 'measurement-document',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent6',
                'url_path': '/fiori/neonatologia/rn/list/',
                'module_name': 'fiori.neonatologia',
                'category': categories['Neonatología'],
                'required_permissions': ['neonatology.view_reciennacido'],
                'allowed_groups': [matrona, supervisor, medico, enfermero],
                'is_transactional': True,
                'default_order': 6
            },
            {
                'app_id': 'tamizajes-metabolicos',
                'title': 'Tamizajes Metabólicos',
                'subtitle': 'PKU y tamizaje neonatal',
                'description': 'Registro y seguimiento de tamizajes metabólicos (PKU) en recién nacidos.',
                'icon': 'lab',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent7',
                'url_path': '/fiori/neonatologia/tamizajes/metabolicos/',
                'module_name': 'fiori.neonatologia',
                'category': categories['Neonatología'],
                'required_permissions': ['neonatology.view_rntamizajemetabolico'],
                'allowed_groups': [matrona, supervisor, medico, enfermero],
                'is_transactional': True,
                'default_order': 7
            },
            {
                'app_id': 'tamizajes-auditivos',
                'title': 'Tamizajes Auditivos',
                'subtitle': 'Detección de hipoacusia',
                'description': 'Registro de tamizajes auditivos (OEA) en recién nacidos para detección precoz de hipoacusia.',
                'icon': 'sound',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent8',
                'url_path': '/fiori/neonatologia/tamizajes/auditivos/',
                'module_name': 'fiori.neonatologia',
                'category': categories['Neonatología'],
                'required_permissions': ['neonatology.view_rntamizajeauditivo'],
                'allowed_groups': [matrona, supervisor, medico, enfermero],
                'is_transactional': True,
                'default_order': 8
            },
            {
                'app_id': 'tamizajes-cardiopatia',
                'title': 'Tamizajes Cardiopatía',
                'subtitle': 'Detección de cardiopatías congénitas',
                'description': 'Registro de tamizajes de oximetría de pulso para detección de cardiopatías congénitas.',
                'icon': 'electrocardiogram',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent9',
                'url_path': '/fiori/neonatologia/tamizajes/cardiopatia/',
                'module_name': 'fiori.neonatologia',
                'category': categories['Neonatología'],
                'required_permissions': ['neonatology.view_rntamizajecardiopatia'],
                'allowed_groups': [matrona, supervisor, medico, enfermero],
                'is_transactional': True,
                'default_order': 9
            },
            {
                'app_id': 'egresos-rn',
                'title': 'Egresos de RN',
                'subtitle': 'Alta de recién nacidos',
                'description': 'Gestión de egresos de recién nacidos, incluyendo tipo de alimentación y anticoncepción al alta.',
                'icon': 'sys-exit',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent10',
                'url_path': '/fiori/neonatologia/egresos/',
                'module_name': 'fiori.neonatologia',
                'category': categories['Neonatología'],
                'required_permissions': ['neonatology.view_rnegreso'],
                'allowed_groups': [matrona, supervisor, medico, enfermero, administrativo],
                'is_transactional': True,
                'default_order': 10
            },
            
            # ========== REPORTES ==========
            {
                'app_id': 'reportes-rem',
                'title': 'Reportes REM',
                'subtitle': 'Generación de Reportes Estadísticos Mensuales',
                'description': 'Generación automática de reportes REM para envío al MINSAL.',
                'icon': 'document',
                'tile_type': 'standard',
                'tile_size': '1x2',
                'background_color': 'Accent1',
                'url_path': '/fiori/reportes/rem/',
                'module_name': 'fiori.reportes',
                'category': categories['Reportes'],
                'required_permissions': ['reports.view_reporterem'],
                'allowed_groups': [supervisor],
                'is_transactional': False,
                'default_order': 11
            },
            {
                'app_id': 'reportes-dashboard',
                'title': 'Dashboard de Estadísticas',
                'subtitle': 'Indicadores y métricas del sistema',
                'description': 'Dashboard con indicadores clave, gráficos y estadísticas del sistema hospitalario.',
                'icon': 'business-objects-experience',
                'tile_type': 'numeric',
                'tile_size': '2x2',
                'background_color': 'Accent2',
                'url_path': '/fiori/reportes/dashboard/',
                'module_name': 'fiori.reportes',
                'category': categories['Reportes'],
                'required_permissions': ['reports.view_reporterem'],
                'allowed_groups': [supervisor],
                'is_transactional': False,
                'default_order': 12
            },
            
            # ========== ADMINISTRACIÓN ==========
            {
                'app_id': 'usuarios-list',
                'title': 'Gestión de Usuarios',
                'subtitle': 'Administración de usuarios y roles',
                'description': 'Gestión completa de usuarios del sistema, asignación de roles y permisos.',
                'icon': 'employee',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent3',
                'url_path': '/fiori/usuarios/list/',
                'module_name': 'fiori.usuarios',
                'category': categories['Administración'],
                'required_permissions': ['core.view_usuario'],
                'allowed_groups': [supervisor],
                'is_transactional': True,
                'default_order': 13
            },
            {
                'app_id': 'auditoria-trazas',
                'title': 'Auditoría del Sistema',
                'subtitle': 'Consulta de trazas y logs',
                'description': 'Consulta completa de auditoría del sistema, trazas de movimientos y accesos.',
                'icon': 'activities',
                'tile_type': 'standard',
                'tile_size': '1x1',
                'background_color': 'Accent4',
                'url_path': '/fiori/auditoria/trazas/',
                'module_name': 'fiori.auditoria',
                'category': categories['Administración'],
                'required_permissions': ['compliance.view_trazamovimiento'],
                'allowed_groups': [supervisor],
                'is_transactional': False,
                'default_order': 14
            },
            {
                'app_id': 'alertas-sistema',
                'title': 'Alertas del Sistema',
                'subtitle': 'Gestión de alertas y notificaciones',
                'description': 'Visualización y resolución de alertas del sistema.',
                'icon': 'alert',
                'tile_type': 'feed',
                'tile_size': '1x1',
                'background_color': 'Accent5',
                'url_path': '/fiori/alertas/',
                'module_name': 'fiori',
                'category': categories['Administración'],
                'required_permissions': ['alerts.view_alertasistema'],
                'allowed_groups': [matrona, supervisor, medico, enfermero, administrativo],
                'is_transactional': False,
                'default_order': 15
            }
        ]
        
        apps_created = 0
        for app_data in apps_data:
            allowed_groups = app_data.pop('allowed_groups')
            
            app, created = FioriApp.objects.get_or_create(
                app_id=app_data['app_id'],
                defaults=app_data
            )
            
            if created:
                # Asignar grupos permitidos
                app.allowed_groups.set(allowed_groups)
                apps_created += 1
                self.stdout.write(f'  ✓ App creada: {app.title}')
            else:
                self.stdout.write(f'  • App existente: {app.title}')
        
        return apps_created