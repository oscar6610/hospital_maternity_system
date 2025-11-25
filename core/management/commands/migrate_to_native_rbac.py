from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Usuario
from django.db import transaction


class Command(BaseCommand):
    help = 'Configura Groups y Permissions nativos de Django para el sistema RBAC'
    
    # Mapeo de nombres de roles
    GROUPS = [
        'Matrona Clínica',
        'Supervisor/Jefe de Área',
        'Médico(a)',
        'Enfermero(a)',
        'Administrativo(a)',
    ]
    
    # Definición completa de permisos por grupo
    # Formato: 'app_label.codename'
    GROUP_PERMISSIONS = {
        'Matrona Clínica': [
            # CATALOGS - Lectura
            'catalogs.view_catnacionalidad',
            'catalogs.view_catpueblooriginario',
            'catalogs.view_catcomplicacionparto',
            'catalogs.view_catrobson',
            'catalogs.view_cattipoparto',
            
            # MATERNITY - Madres
            'maternity.add_madrepaciente',
            'maternity.view_madrepaciente',
            'maternity.change_madrepaciente',
            
            # MATERNITY - Embarazos
            'maternity.add_embarazo',
            'maternity.view_embarazo',
            'maternity.change_embarazo',
            
            # MATERNITY - Partos
            'maternity.add_parto',
            'maternity.view_parto',
            'maternity.change_parto',  # Con restricción de turno en lógica
            
            # MATERNITY - Complicaciones
            'maternity.add_partocomplicacion',
            'maternity.view_partocomplicacion',
            'maternity.change_partocomplicacion',
            
            # MATERNITY - Anestesias
            'maternity.add_partoanestesia',
            'maternity.view_partoanestesia',
            
            # MATERNITY - IVE
            'maternity.add_iveatencion',
            'maternity.view_iveatencion',
            'maternity.change_iveatencion',
            'maternity.add_iveacompanamiento',
            'maternity.view_iveacompanamiento',
            
            # MATERNITY - Anticonceptivos
            'maternity.add_altaanticonceptivo',
            'maternity.view_altaanticonceptivo',
            'maternity.change_altaanticonceptivo',
            
            # NEONATOLOGY - Recién Nacidos
            'neonatology.add_reciennacido',
            'neonatology.view_reciennacido',
            'neonatology.change_reciennacido',
            
            # NEONATOLOGY - Atención Inmediata
            'neonatology.add_rnatencioninmediata',
            'neonatology.view_rnatencioninmediata',
            'neonatology.change_rnatencioninmediata',
            
            # NEONATOLOGY - Tamizajes
            'neonatology.add_rntamizajemetabolico',
            'neonatology.view_rntamizajemetabolico',
            'neonatology.change_rntamizajemetabolico',
            'neonatology.add_rntamizajeauditivo',
            'neonatology.view_rntamizajeauditivo',
            'neonatology.change_rntamizajeauditivo',
            'neonatology.add_rntamizajecardiopatia',
            'neonatology.view_rntamizajecardiopatia',
            'neonatology.change_rntamizajecardiopatia',
            
            # NEONATOLOGY - Egresos
            'neonatology.add_rnegreso',
            'neonatology.view_rnegreso',
            'neonatology.change_rnegreso',
            
            # ALERTS
            'alerts.view_alertasistema',
        ],
        
        'Supervisor/Jefe de Área': [
            # CATALOGS - Gestión completa
            'catalogs.add_catnacionalidad',
            'catalogs.view_catnacionalidad',
            'catalogs.change_catnacionalidad',
            'catalogs.delete_catnacionalidad',
            'catalogs.add_catpueblooriginario',
            'catalogs.view_catpueblooriginario',
            'catalogs.change_catpueblooriginario',
            'catalogs.delete_catpueblooriginario',
            'catalogs.add_catcomplicacionparto',
            'catalogs.view_catcomplicacionparto',
            'catalogs.change_catcomplicacionparto',
            'catalogs.add_catrobson',
            'catalogs.view_catrobson',
            'catalogs.change_catrobson',
            'catalogs.add_cattipoparto',
            'catalogs.view_cattipoparto',
            'catalogs.change_cattipoparto',
            
            # MATERNITY - Acceso completo
            'maternity.add_madrepaciente',
            'maternity.view_madrepaciente',
            'maternity.change_madrepaciente',
            'maternity.delete_madrepaciente',
            'maternity.add_embarazo',
            'maternity.view_embarazo',
            'maternity.change_embarazo',
            'maternity.delete_embarazo',
            'maternity.add_parto',
            'maternity.view_parto',
            'maternity.change_parto',
            'maternity.delete_parto',
            'maternity.add_partocomplicacion',
            'maternity.view_partocomplicacion',
            'maternity.change_partocomplicacion',
            'maternity.delete_partocomplicacion',
            'maternity.add_partoanestesia',
            'maternity.view_partoanestesia',
            'maternity.change_partoanestesia',
            'maternity.add_iveatencion',
            'maternity.view_iveatencion',
            'maternity.change_iveatencion',
            'maternity.delete_iveatencion',
            'maternity.add_iveacompanamiento',
            'maternity.view_iveacompanamiento',
            'maternity.change_iveacompanamiento',
            'maternity.add_altaanticonceptivo',
            'maternity.view_altaanticonceptivo',
            'maternity.change_altaanticonceptivo',
            
            # NEONATOLOGY - Acceso completo
            'neonatology.add_reciennacido',
            'neonatology.view_reciennacido',
            'neonatology.change_reciennacido',
            'neonatology.delete_reciennacido',
            'neonatology.add_rnatencioninmediata',
            'neonatology.view_rnatencioninmediata',
            'neonatology.change_rnatencioninmediata',
            'neonatology.add_rntamizajemetabolico',
            'neonatology.view_rntamizajemetabolico',
            'neonatology.change_rntamizajemetabolico',
            'neonatology.add_rntamizajeauditivo',
            'neonatology.view_rntamizajeauditivo',
            'neonatology.change_rntamizajeauditivo',
            'neonatology.add_rntamizajecardiopatia',
            'neonatology.view_rntamizajecardiopatia',
            'neonatology.change_rntamizajecardiopatia',
            'neonatology.add_rnegreso',
            'neonatology.view_rnegreso',
            'neonatology.change_rnegreso',
            
            # REPORTS
            'reports.add_reporterem',
            'reports.view_reporterem',
            'reports.change_reporterem',
            'reports.delete_reporterem',
            'reports.add_reporteremdetalle',
            'reports.view_reporteremdetalle',
            
            # ALERTS
            'alerts.view_alertasistema',
            'alerts.change_alertasistema',
            
            # COMPLIANCE
            'compliance.view_trazamovimiento',
            
            # CORE - Gestión de usuarios
            'core.add_usuario',
            'core.view_usuario',
            'core.change_usuario',
            'core.delete_usuario',
            
            # AUTH - Gestión de grupos (roles)
            'auth.add_group',
            'auth.view_group',
            'auth.change_group',
            'auth.delete_group',
        ],
        
        'Médico(a)': [
            # CATALOGS - Lectura
            'catalogs.view_catnacionalidad',
            'catalogs.view_catpueblooriginario',
            'catalogs.view_catcomplicacionparto',
            'catalogs.view_catrobson',
            'catalogs.view_cattipoparto',
            
            # MATERNITY - Lectura y actualización
            'maternity.view_madrepaciente',
            'maternity.change_madrepaciente',
            'maternity.view_embarazo',
            'maternity.view_parto',
            'maternity.change_parto',  # Sin restricción de turno
            'maternity.view_partocomplicacion',
            'maternity.change_partocomplicacion',
            'maternity.add_partocomplicacion',
            'maternity.view_altaanticonceptivo',
            'maternity.change_altaanticonceptivo',
            
            # NEONATOLOGY - Lectura
            'neonatology.view_reciennacido',
            'neonatology.view_rntamizajemetabolico',
            'neonatology.change_rntamizajemetabolico',
            'neonatology.view_rntamizajeauditivo',
            'neonatology.view_rntamizajecardiopatia',
            'neonatology.view_rnegreso',
            'neonatology.change_rnegreso',
            
            # ALERTS
            'alerts.view_alertasistema',
        ],
        
        'Enfermero(a)': [
            # CATALOGS - Lectura
            'catalogs.view_catnacionalidad',
            'catalogs.view_catpueblooriginario',
            'catalogs.view_catcomplicacionparto',
            'catalogs.view_catrobson',
            'catalogs.view_cattipoparto',
            
            # MATERNITY - Solo lectura
            'maternity.view_madrepaciente',
            'maternity.view_parto',
            
            # NEONATOLOGY - Atención inmediata y tamizajes
            'neonatology.view_reciennacido',
            'neonatology.add_rnatencioninmediata',
            'neonatology.view_rnatencioninmediata',
            'neonatology.change_rnatencioninmediata',
            'neonatology.add_rntamizajemetabolico',
            'neonatology.view_rntamizajemetabolico',
            'neonatology.change_rntamizajemetabolico',
            'neonatology.add_rntamizajeauditivo',
            'neonatology.view_rntamizajeauditivo',
            'neonatology.change_rntamizajeauditivo',
            'neonatology.add_rntamizajecardiopatia',
            'neonatology.view_rntamizajecardiopatia',
            'neonatology.change_rntamizajecardiopatia',
            'neonatology.add_rnegreso',
            'neonatology.view_rnegreso',
            'neonatology.change_rnegreso',
            
            # ALERTS
            'alerts.view_alertasistema',
        ],
        
        'Administrativo(a)': [
            # CATALOGS - Lectura
            'catalogs.view_catnacionalidad',
            'catalogs.view_catpueblooriginario',
            'catalogs.view_catcomplicacionparto',
            'catalogs.view_catrobson',
            'catalogs.view_cattipoparto',
            
            # MATERNITY - Ingreso de madres
            'maternity.add_madrepaciente',
            'maternity.view_madrepaciente',
            'maternity.change_madrepaciente',
            'maternity.view_parto',
            
            # NEONATOLOGY - Solo lectura
            'neonatology.view_reciennacido',
            'neonatology.add_rnegreso',
            'neonatology.view_rnegreso',
            'neonatology.change_rnegreso',
            
            # ALERTS
            'alerts.view_alertasistema',
        ],
    }
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚀 Configurando sistema RBAC nativo...'))
        
        # Paso 1: Crear/obtener Groups
        self.stdout.write('\n📁 Creando/verificando Groups...')
        groups = {}
        for group_name in self.GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)
            groups[group_name] = group
            status = '✅ Creado' if created else '✓ Ya existe'
            self.stdout.write(f'  {status}: {group_name}')
        
        # Paso 2: Asignar permisos a Groups
        self.stdout.write('\n🔐 Asignando permisos a Groups...')
        
        permisos_no_encontrados = []
        
        for group_name, permission_codes in self.GROUP_PERMISSIONS.items():
            group = groups[group_name]
            
            # Limpiar permisos existentes
            group.permissions.clear()
            
            permisos_asignados = 0
            for perm_code in permission_codes:
                try:
                    app_label, codename = perm_code.split('.')
                    perm = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    group.permissions.add(perm)
                    permisos_asignados += 1
                except Permission.DoesNotExist:
                    permisos_no_encontrados.append(perm_code)
                    self.stdout.write(self.style.ERROR(
                        f'  ❌ Permiso no encontrado: {perm_code}'
                    ))
                except ValueError:
                    self.stdout.write(self.style.ERROR(
                        f'  ❌ Formato inválido: {perm_code} (debe ser app_label.codename)'
                    ))
            
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ {group_name}: {permisos_asignados}/{len(permission_codes)} permisos asignados'
            ))
        
        # Paso 3: Reporte de permisos faltantes
        if permisos_no_encontrados:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️ {len(permisos_no_encontrados)} permisos no encontrados:'
            ))
            for perm in set(permisos_no_encontrados):
                self.stdout.write(f'  - {perm}')
            self.stdout.write(self.style.WARNING(
                '\n💡 TIP: Ejecuta las migraciones de todas las apps para generar permisos automáticamente'
            ))
        
        # Paso 4: Estadísticas finales
        self.stdout.write(self.style.SUCCESS(f'\n✅ Configuración completada!'))
        self.stdout.write(f'  📊 {len(groups)} grupos configurados')
        
        total_permisos = sum([g.permissions.count() for g in groups.values()])
        self.stdout.write(f'  🔐 {total_permisos} permisos asignados en total')
        
        # Paso 5: Sugerencia de siguiente paso
        usuarios_sin_grupo = Usuario.objects.filter(groups__isnull=True).count()
        if usuarios_sin_grupo > 0:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️ Hay {usuarios_sin_grupo} usuarios sin grupo asignado'
            ))
            self.stdout.write(self.style.WARNING(
                '💡 Asígnalos manualmente en el admin de Django'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            '\n✅ Sistema listo para usar permisos nativos de Django'
        ))