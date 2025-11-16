from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Rol, Permiso, RolPermiso

Usuario = get_user_model()


class UsuarioModelTest(TestCase):
    """Tests para el modelo Usuario basado en AbstractUser"""
    
    def setUp(self):
        self.rol = Rol.objects.create(nombre_rol='Médico')
    
    def test_create_usuario(self):
        """Crear un usuario con UsuarioManager"""
        user = Usuario.objects.create_user(
            run='12345678-9',
            email='doctor@hospital.com',
            password='testpass123',
            nombre_completo='Dr. Juan García',
            fk_rol=self.rol
        )
        self.assertEqual(user.run, '12345678-9')
        self.assertEqual(user.nombre_completo, 'Dr. Juan García')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNotNone(user.id_usuario)
    
    def test_create_superuser(self):
        """Crear un superusuario"""
        admin = Usuario.objects.create_superuser(
            run='admin123-4',
            email='admin@hospital.com',
            password='adminpass123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password('adminpass123'))
    
    def test_run_unique(self):
        """El run debe ser único"""
        Usuario.objects.create_user(
            run='12345678-9',
            email='doctor1@hospital.com',
            password='testpass123',
            nombre_completo='Dr. Juan García'
        )
        with self.assertRaises(Exception):
            Usuario.objects.create_user(
                run='12345678-9',
                email='doctor2@hospital.com',
                password='testpass123',
                nombre_completo='Dr. Carlos López'
            )
    
    def test_email_unique(self):
        """El email debe ser único"""
        Usuario.objects.create_user(
            run='11111111-1',
            email='doctor@hospital.com',
            password='testpass123',
            nombre_completo='Dr. Juan García'
        )
        with self.assertRaises(Exception):
            Usuario.objects.create_user(
                run='22222222-2',
                email='doctor@hospital.com',
                password='testpass123',
                nombre_completo='Dr. Carlos López'
            )
    
    def test_username_field_is_run(self):
        """USERNAME_FIELD debe ser 'run'"""
        self.assertEqual(Usuario.USERNAME_FIELD, 'run')


class UsuarioAuthenticationAPITest(APITestCase):
    """Tests para autenticación JWT"""
    
    def setUp(self):
        self.client = APIClient()
        self.rol = Rol.objects.create(nombre_rol='Enfermera')
        self.user = Usuario.objects.create_user(
            run='12345678-9',
            email='nurse@hospital.com',
            password='testpass123',
            nombre_completo='Enfermera María',
            fk_rol=self.rol
        )
    
    def test_token_obtain(self):
        """Obtener tokens JWT con credenciales válidas"""
        response = self.client.post('/api/auth/token/', {
            'run': '12345678-9',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['run'], '12345678-9')
    
    def test_token_obtain_invalid_credentials(self):
        """Fallar al obtener tokens con credenciales inválidas"""
        response = self.client.post('/api/auth/token/', {
            'run': '12345678-9',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_token_obtain_missing_fields(self):
        """Fallar al obtener tokens sin run o password"""
        response = self.client.post('/api/auth/token/', {
            'run': '12345678-9'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_protected_endpoint_without_token(self):
        """Acceso denegado sin token en endpoint protegido"""
        response = self.client.get('/api/usuarios/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_with_token(self):
        """Acceso permitido con token válido"""
        # Obtener token
        token_response = self.client.post('/api/auth/token/', {
            'run': '12345678-9',
            'password': 'testpass123'
        })
        access_token = token_response.data['access']
        
        # Usar token para acceder endpoint protegido
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/usuarios/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['run'], '12345678-9')


class ChangePasswordAPITest(APITestCase):
    """Tests para cambio de contraseña"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            run='87654321-1',
            email='user@hospital.com',
            password='oldpass123',
            nombre_completo='User Test'
        )
        # Autenticar
        token_response = self.client.post('/api/auth/token/', {
            'run': '87654321-1',
            'password': 'oldpass123'
        })
        self.access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_change_password_success(self):
        """Cambiar contraseña exitosamente"""
        response = self.client.post(
            f'/api/usuarios/{self.user.id_usuario}/change_password/',
            {
                'old_password': 'oldpass123',
                'new_password': 'newpass456',
                'new_password_confirm': 'newpass456'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la nueva contraseña funciona
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))
    
    def test_change_password_wrong_old_password(self):
        """Fallar al cambiar contraseña con contraseña antigua incorrecta"""
        response = self.client.post(
            f'/api/usuarios/{self.user.id_usuario}/change_password/',
            {
                'old_password': 'wrongoldpass',
                'new_password': 'newpass456',
                'new_password_confirm': 'newpass456'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_mismatch(self):
        """Fallar si las nuevas contraseñas no coinciden"""
        response = self.client.post(
            f'/api/usuarios/{self.user.id_usuario}/change_password/',
            {
                'old_password': 'oldpass123',
                'new_password': 'newpass456',
                'new_password_confirm': 'differentpass'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_too_short(self):
        """Fallar si la nueva contraseña es muy corta"""
        response = self.client.post(
            f'/api/usuarios/{self.user.id_usuario}/change_password/',
            {
                'old_password': 'oldpass123',
                'new_password': 'short',
                'new_password_confirm': 'short'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RolPermisoTest(TestCase):
    """Tests para Rol, Permiso y RolPermiso"""
    
    def test_create_rol(self):
        """Crear un rol"""
        rol = Rol.objects.create(nombre_rol='Administrador')
        self.assertEqual(rol.nombre_rol, 'Administrador')
    
    def test_rol_unique(self):
        """El nombre del rol debe ser único"""
        Rol.objects.create(nombre_rol='Doctor')
        with self.assertRaises(Exception):
            Rol.objects.create(nombre_rol='Doctor')
    
    def test_create_permiso(self):
        """Crear un permiso"""
        permiso = Permiso.objects.create(codigo_permiso='ver_pacientes')
        self.assertEqual(permiso.codigo_permiso, 'ver_pacientes')
    
    def test_rol_permiso_relationship(self):
        """Crear asociación entre Rol y Permiso"""
        rol = Rol.objects.create(nombre_rol='Editor')
        permiso = Permiso.objects.create(codigo_permiso='editar_datos')
        rol_permiso = RolPermiso.objects.create(fk_rol=rol, fk_permiso=permiso)
        
        self.assertEqual(rol_permiso.fk_rol, rol)
        self.assertEqual(rol_permiso.fk_permiso, permiso)
    
    def test_rol_permiso_unique_together(self):
        """Un rol no puede tener el mismo permiso dos veces"""
        rol = Rol.objects.create(nombre_rol='Viewer')
        permiso = Permiso.objects.create(codigo_permiso='view_only')
        RolPermiso.objects.create(fk_rol=rol, fk_permiso=permiso)
        
        with self.assertRaises(Exception):
            RolPermiso.objects.create(fk_rol=rol, fk_permiso=permiso)

