from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Permiso, Rol, RolPermiso


class Command(BaseCommand):
    help = 'Carga los permisos y roles del sistema RBAC'

    def handle(self, *args, **options):
        from django.utils import timezone
        from datetime import datetime
        now = timezone.now()
        
        # Datos de permisos
        permisos_data = [
            ('catalog:read', 'Consultar Catálogos', 'Permiso para consultar listas estandarizadas como Grupos de Robson o complicaciones.', 'catalog'),
            ('catalog:manage', 'Gestionar Catálogos', 'Permiso para crear, modificar o eliminar clasificaciones estandarizadas.', 'catalog'),
            ('maternity:mother:create', 'Crear Madre Paciente', 'Registrar nuevos ingresos de madres.', 'maternity'),
            ('maternity:mother:read', 'Consultar Madre Paciente', 'Consultar antecedentes y datos de la paciente.', 'maternity'),
            ('maternity:mother:update', 'Actualizar Madre Paciente', 'Modificar datos demográficos o antecedentes.', 'maternity'),
            ('maternity:delivery:create', 'Registrar Parto', 'Registrar un nuevo evento de parto.', 'maternity'),
            ('maternity:delivery:read', 'Consultar Parto', 'Consultar datos de partos.', 'maternity'),
            ('maternity:delivery:update_own', 'Actualizar Parto (Propio/Turno)', 'Modificar solo los registros de partos creados por ella o en su turno.', 'maternity'),
            ('maternity:delivery:update_all', 'Actualizar Parto (Todos)', 'Permiso para modificar cualquier registro de parto sin restricción de turno.', 'maternity'),
            ('maternity:ive:manage', 'Gestionar IVE', 'Registrar y modificar atenciones de IVE, incluyendo acompañamiento.', 'maternity'),
            ('maternity:complication:manage', 'Gestionar Complicaciones', 'Registrar complicaciones como HPP o Preeclampsia.', 'maternity'),
            ('maternity:contraceptive:manage', 'Gestionar Anticoncepción', 'Registrar el método anticonceptivo al alta.', 'maternity'),
            ('neonatal:rn:create', 'Registrar Recién Nacido', 'Registrar un Recién Nacido.', 'neonatology'),
            ('neonatal:rn:read', 'Consultar Recién Nacido', 'Consultar el registro del RN y su trazabilidad.', 'neonatology'),
            ('neonatal:rn:update_immediate', 'Registrar Datos Inmediatos RN', 'Registrar APGAR, contacto piel a piel, y profilaxis.', 'neonatology'),
            ('neonatal:tamizaje:manage', 'Gestionar Tamizaje', 'Registrar y modificar tamizajes: Metabólico, Auditivo, Cardiopatía.', 'neonatology'),
            ('neonatal:discharge:manage', 'Gestionar Alta Neonatal', 'Registrar egreso y tipo de alimentación al alta.', 'neonatology'),
            ('report:generate_rem', 'Generar Reporte REM', 'Único permiso para la generación automática del reporte REM BS22 - Atenciones de Obstetricia y Ginecología.', 'reports'),
            ('report:export_data', 'Exportar Datos', 'Función simple para exportar la data cruda a Excel.', 'reports'),
            ('alert:read', 'Visualizar Alertas', 'Visualizar alertas de datos incompletos o críticos.', 'alerts'),
            ('alert:resolve', 'Resolver Alertas', 'Marcar alertas como resueltas.', 'alerts'),
            ('compliance:audit:read', 'Consultar Auditoría', 'Consultar el registro de auditoría de acciones, esencial para la seguridad.', 'compliance'),
            ('core:user:manage', 'Gestionar Usuarios', 'Crear, editar y eliminar usuarios.', 'core'),
            ('core:role:manage', 'Gestionar Roles', 'Administrar roles, perfiles y permisos de RBAC.', 'core'),
        ]
        
        # Crear permisos
        permisos = {}
        for codigo, nombre, descripcion, categoria in permisos_data:
            permiso, created = Permiso.objects.get_or_create(
                codigo_permiso=codigo,
                defaults={
                    'nombre_permiso': nombre,
                    'descripcion': descripcion,
                    'categoria': categoria,
                    'activo': True,
                }
            )
            permisos[codigo] = permiso
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Permiso creado: {codigo}'))
        
        # Datos de roles
        roles_data = [
            ('matrona_clinica', 'Matrona Clínica - Responsable de registrar datos del parto y recién nacido. Solo puede modificar registros de su turno.'),
            ('supervisor_jefe', 'Supervisor/Jefe de Área - Acceso completo a todos los datos, consulta reportes y estadísticas.'),
            ('medico', 'Médico(a) - Consulta información clínica y actualiza estados de salud. Responsable de gestión de complicaciones.'),
            ('enfermero', 'Enfermero(a) - Registra procedimientos y administración de medicamentos, enfocándose en atención inmediata y tamizajes.'),
            ('administrativo', 'Administrativo(a) - Gestiona datos de ingreso de la madre y coordina el proceso de alta.'),
        ]
        
        # Crear roles
        roles = {}
        for nombre_rol, descripcion in roles_data:
            rol, created = Rol.objects.get_or_create(
                nombre_rol=nombre_rol,
                defaults={'descripcion': descripcion}
            )
            roles[nombre_rol] = rol
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Rol creado: {nombre_rol}'))
        
        # Definir permisos por rol
        rol_permisos_mapping = {
            'matrona_clinica': [
                'catalog:read',
                'maternity:mother:create',
                'maternity:mother:read',
                'maternity:mother:update',
                'maternity:delivery:create',
                'maternity:delivery:read',
                'maternity:delivery:update_own',
                'maternity:ive:manage',
                'maternity:complication:manage',
                'maternity:contraceptive:manage',
                'neonatal:rn:create',
                'neonatal:rn:read',
                'neonatal:rn:update_immediate',
                'neonatal:tamizaje:manage',
                'neonatal:discharge:manage',
                'alert:read',
            ],
            'supervisor_jefe': [
                'catalog:read',
                'catalog:manage',
                'core:user:manage',
                'core:role:manage',
                'maternity:mother:create',
                'maternity:mother:read',
                'maternity:mother:update',
                'maternity:delivery:create',
                'maternity:delivery:read',
                'maternity:delivery:update_all',
                'maternity:ive:manage',
                'maternity:complication:manage',
                'maternity:contraceptive:manage',
                'neonatal:rn:create',
                'neonatal:rn:read',
                'neonatal:rn:update_immediate',
                'neonatal:tamizaje:manage',
                'neonatal:discharge:manage',
                'report:generate_rem',
                'report:export_data',
                'alert:read',
                'alert:resolve',
                'compliance:audit:read',
            ],
            'medico': [
                'catalog:read',
                'maternity:mother:read',
                'maternity:mother:update',
                'maternity:delivery:read',
                'maternity:delivery:update_all',
                'maternity:complication:manage',
                'maternity:contraceptive:manage',
                'neonatal:rn:read',
                'neonatal:tamizaje:manage',
                'neonatal:discharge:manage',
                'alert:read',
            ],
            'enfermero': [
                'catalog:read',
                'maternity:mother:read',
                'maternity:delivery:read',
                'neonatal:rn:read',
                'neonatal:rn:update_immediate',
                'neonatal:tamizaje:manage',
                'neonatal:discharge:manage',
                'alert:read',
            ],
            'administrativo': [
                'catalog:read',
                'maternity:mother:create',
                'maternity:mother:read',
                'maternity:mother:update',
                'maternity:delivery:read',
                'neonatal:rn:read',
                'neonatal:discharge:manage',
                'alert:read',
            ],
        }
        
        # Asignar permisos a roles
        for nombre_rol, codigos_permisos in rol_permisos_mapping.items():
            rol = roles[nombre_rol]
            for codigo_permiso in codigos_permisos:
                permiso = permisos[codigo_permiso]
                rol_permiso, created = RolPermiso.objects.get_or_create(
                    fk_rol=rol,
                    fk_permiso=permiso
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Permiso {codigo_permiso} asignado a {nombre_rol}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Sistema RBAC cargado exitosamente'))
