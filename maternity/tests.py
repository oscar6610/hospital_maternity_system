from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model

from .models import (
    MadrePaciente, Embarazo, Parto, PartoComplicacion,
    PartoAnestesia, IVEAtencion, IVEAcompanamiento, AltaAnticonceptivo
)
from catalogs.models import CatNacionalidad, CatPuebloOriginario, CatTipoParto, CatComplicacionParto, CatRobson

Usuario = get_user_model()


class MadrePacienteTestCase(TestCase):
    """Pruebas para modelo MadrePaciente."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
        cls.pueblo_originario = CatPuebloOriginario.objects.create(nombre='Mapuche')
    
    def setUp(self):
        self.madre_data = {
            'run': '12345678-9',
            'nombre': 'María',
            'apellido_paterno': 'García',
            'apellido_materno': 'López',
            'fecha_nacimiento': date(1990, 5, 15),
            'fk_nacionalidad': self.nacionalidad,
            'fk_pueblo_originario': self.pueblo_originario,
        }
    
    def test_madre_creation(self):
        """Test creación de madre."""
        madre = MadrePaciente.objects.create(**self.madre_data)
        self.assertEqual(madre.run, '12345678-9')
        self.assertEqual(madre.nombre, 'María')
        self.assertIsNotNone(madre.fecha_registro)
    
    def test_nombre_completo(self):
        """Test método nombre_completo()."""
        madre = MadrePaciente.objects.create(**self.madre_data)
        self.assertEqual(madre.nombre_completo(), 'María García López')
    
    def test_edad_validation(self):
        """Test validación de edad."""
        # Edad válida
        madre = MadrePaciente.objects.create(**self.madre_data)
        madre.clean()  # No debe lanzar excepción
        
        # Edad inválida (futura)
        madre_futura = MadrePaciente(
            run='99999999-9',
            nombre='Test',
            apellido_paterno='Test',
            apellido_materno='Test',
            fecha_nacimiento=date.today() + timedelta(days=1),
            fk_nacionalidad=self.nacionalidad,
        )
        with self.assertRaises(ValidationError):
            madre_futura.full_clean()
    
    def test_run_unique(self):
        """Test que RUN es único."""
        MadrePaciente.objects.create(**self.madre_data)
        madre_duplicada = MadrePaciente(**self.madre_data)
        with self.assertRaises(Exception):  # IntegrityError
            madre_duplicada.save()


class EmbarazoTestCase(TestCase):
    """Pruebas para modelo Embarazo."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
    
    def setUp(self):
        self.madre = MadrePaciente.objects.create(
            run='11111111-1',
            nombre='Ana',
            apellido_paterno='Pérez',
            apellido_materno='Silva',
            fecha_nacimiento=date(1985, 1, 1),
            fk_nacionalidad=self.nacionalidad,
        )
    
    def test_embarazo_creation(self):
        """Test creación de embarazo."""
        embarazo = Embarazo.objects.create(
            fk_madre=self.madre,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=20),
            semana_obstetrica=20,
            paridad=0,
            control_prenatal=True
        )
        self.assertEqual(embarazo.fk_madre, self.madre)
        self.assertEqual(embarazo.semana_obstetrica, 20)
    
    def test_obtener_trimestre(self):
        """Test cálculo de trimestre."""
        # Primer trimestre
        emb1 = Embarazo.objects.create(
            fk_madre=self.madre,
            fecha_ultima_menstruacion=date.today(),
            semana_obstetrica=8,
            paridad=0,
            control_prenatal=True
        )
        self.assertEqual(emb1.obtener_trimestre(), 1)
        
        # Segundo trimestre
        emb2 = Embarazo.objects.create(
            fk_madre=self.madre,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=15),
            semana_obstetrica=15,
            paridad=0,
            control_prenatal=True
        )
        self.assertEqual(emb2.obtener_trimestre(), 2)
        
        # Tercer trimestre
        emb3 = Embarazo.objects.create(
            fk_madre=self.madre,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=30),
            semana_obstetrica=30,
            paridad=0,
            control_prenatal=True
        )
        self.assertEqual(emb3.obtener_trimestre(), 3)
    
    def test_es_embarazo_viable(self):
        """Test si embarazo es viable (>= 20 semanas)."""
        embarazo_no_viable = Embarazo.objects.create(
            fk_madre=self.madre,
            fecha_ultima_menstruacion=date.today(),
            semana_obstetrica=19,
            paridad=0,
            control_prenatal=True
        )
        self.assertFalse(embarazo_no_viable.es_embarazo_viables())
        
        embarazo_viable = Embarazo.objects.create(
            fk_madre=self.madre,
            fecha_ultima_menstruacion=date.today() - timedelta(weeks=20),
            semana_obstetrica=20,
            paridad=0,
            control_prenatal=True
        )
        self.assertTrue(embarazo_viable.es_embarazo_viables())


class PartoTestCase(TestCase):
    """Pruebas para modelo Parto."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
        cls.tipo_parto = CatTipoParto.objects.create(nombre='Vaginal')
        cls.robson = CatRobson.objects.create(grupo='1', descripcion='Multíparas sin cicatriz uterina')
    
    def setUp(self):
        self.madre = MadrePaciente.objects.create(
            run='22222222-2',
            nombre='Laura',
            apellido_paterno='Martínez',
            apellido_materno='González',
            fecha_nacimiento=date(1988, 3, 10),
            fk_nacionalidad=self.nacionalidad,
        )
        
        self.profesional = Usuario.objects.create_user(
            run='33333333-3',
            password='test123',
            nombre_completo='Dr. Juan Pérez'
        )
    
    def test_parto_creation(self):
        """Test creación de parto."""
        parto = Parto.objects.create(
            fk_madre=self.madre,
            fk_tipo_parto=self.tipo_parto,
            fk_profesional_responsable=self.profesional,
            fk_clasificacion_robson=self.robson,
            fecha_parto=datetime.now(),
            horas_trabajo_parto=8
        )
        self.assertEqual(parto.fk_madre, self.madre)
        self.assertEqual(parto.horas_trabajo_parto, 8)
    
    def test_tuvo_complicaciones(self):
        """Test detección de complicaciones."""
        parto = Parto.objects.create(
            fk_madre=self.madre,
            fk_tipo_parto=self.tipo_parto,
            fk_profesional_responsable=self.profesional,
            fk_clasificacion_robson=self.robson,
            fecha_parto=datetime.now(),
        )
        
        # Sin complicaciones
        self.assertFalse(parto.tuvo_complicaciones())
        
        # Con complicaciones
        complicacion = CatComplicacionParto.objects.create(nombre='Hemorragia')
        PartoComplicacion.objects.create(fk_parto=parto, fk_complicacion=complicacion)
        self.assertTrue(parto.tuvo_complicaciones())


class PartoComplicacionTestCase(TestCase):
    """Pruebas para modelo PartoComplicacion."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
        cls.tipo_parto = CatTipoParto.objects.create(nombre='Vaginal')
        cls.robson = CatRobson.objects.create(grupo='1', descripcion='Test')
        cls.complicacion = CatComplicacionParto.objects.create(nombre='Hemorragia')
    
    def setUp(self):
        self.madre = MadrePaciente.objects.create(
            run='44444444-4',
            nombre='Paula',
            apellido_paterno='Rodríguez',
            apellido_materno='Díaz',
            fecha_nacimiento=date(1992, 7, 20),
            fk_nacionalidad=self.nacionalidad,
        )
        
        self.profesional = Usuario.objects.create_user(
            run='55555555-5',
            password='test123'
        )
        
        self.parto = Parto.objects.create(
            fk_madre=self.madre,
            fk_tipo_parto=self.tipo_parto,
            fk_profesional_responsable=self.profesional,
            fk_clasificacion_robson=self.robson,
            fecha_parto=datetime.now(),
        )
    
    def test_complicacion_unica_por_parto(self):
        """Test que no haya duplicados de complicación por parto."""
        PartoComplicacion.objects.create(
            fk_parto=self.parto,
            fk_complicacion=self.complicacion
        )
        
        # Intenta crear duplicado
        with self.assertRaises(Exception):  # IntegrityError
            PartoComplicacion.objects.create(
                fk_parto=self.parto,
                fk_complicacion=self.complicacion
            )


class PartoAnestesiaTestCase(TestCase):
    """Pruebas para modelo PartoAnestesia."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
        cls.tipo_parto = CatTipoParto.objects.create(nombre='Vaginal')
        cls.robson = CatRobson.objects.create(grupo='1', descripcion='Test')
    
    def setUp(self):
        self.madre = MadrePaciente.objects.create(
            run='66666666-6',
            nombre='Sandra',
            apellido_paterno='López',
            apellido_materno='Fernández',
            fecha_nacimiento=date(1995, 2, 14),
            fk_nacionalidad=self.nacionalidad,
        )
        
        self.profesional = Usuario.objects.create_user(
            run='77777777-7',
            password='test123'
        )
        
        self.parto = Parto.objects.create(
            fk_madre=self.madre,
            fk_tipo_parto=self.tipo_parto,
            fk_profesional_responsable=self.profesional,
            fk_clasificacion_robson=self.robson,
            fecha_parto=datetime.now(),
        )
    
    def test_anestesia_creation(self):
        """Test creación de anestesia."""
        anestesia = PartoAnestesia.objects.create(
            fk_parto=self.parto,
            tipo_anestesia='epidural',
            solicitada_por_paciente=True
        )
        self.assertEqual(anestesia.tipo_anestesia, 'epidural')
        self.assertTrue(anestesia.solicitada_por_paciente)


class IVEAtencionTestCase(TestCase):
    """Pruebas para modelo IVEAtencion."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
    
    def setUp(self):
        self.madre = MadrePaciente.objects.create(
            run='88888888-8',
            nombre='Carmen',
            apellido_paterno='Silva',
            apellido_materno='Vargas',
            fecha_nacimiento=date(1993, 11, 8),
            fk_nacionalidad=self.nacionalidad,
        )
    
    def test_ive_atencion_creation(self):
        """Test creación de atención IVE."""
        ive = IVEAtencion.objects.create(
            fk_madre=self.madre,
            fk_causal='1',
            edad_gestacional_semanas=12
        )
        self.assertEqual(ive.fk_causal, '1')
        self.assertEqual(ive.edad_gestacional_semanas, 12)
    
    def test_ive_multiple_por_madre(self):
        """Test múltiples IVE por madre."""
        ive1 = IVEAtencion.objects.create(
            fk_madre=self.madre,
            fk_causal='1',
            edad_gestacional_semanas=10
        )
        
        ive2 = IVEAtencion.objects.create(
            fk_madre=self.madre,
            fk_causal='2',
            edad_gestacional_semanas=15
        )
        
        ives = self.madre.ive_atenciones.all()
        self.assertEqual(ives.count(), 2)


class IVEAcompanamientoTestCase(TestCase):
    """Pruebas para modelo IVEAcompanamiento."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nacionalidad = CatNacionalidad.objects.create(nombre='Chilena')
    
    def setUp(self):
        self.madre = MadrePaciente.objects.create(
            run='99999999-9',
            nombre='Rosa',
            apellido_paterno='García',
            apellido_materno='Ruiz',
            fecha_nacimiento=date(1991, 6, 25),
            fk_nacionalidad=self.nacionalidad,
        )
        
        self.ive = IVEAtencion.objects.create(
            fk_madre=self.madre,
            fk_causal='1',
            edad_gestacional_semanas=8
        )
    
    def test_acompanamiento_creation(self):
        """Test creación de acompañamiento."""
        acomp = IVEAcompanamiento.objects.create(
            fk_ive_atencion=self.ive,
            tipo_profesional='psicologo'
        )
        self.assertEqual(acomp.tipo_profesional, 'psicologo')
    
    def test_multiple_acompaniamientos(self):
        """Test múltiples acompañamientos por IVE."""
        IVEAcompanamiento.objects.create(
            fk_ive_atencion=self.ive,
            tipo_profesional='psicologo'
        )
        
        IVEAcompanamiento.objects.create(
            fk_ive_atencion=self.ive,
            tipo_profesional='asistente_social'
        )
        
        acomps = self.ive.acompañamientos.all()
        self.assertEqual(acomps.count(), 2)


class AltaAnticonceptivoTestCase(TestCase):
    """Pruebas para modelo AltaAnticonceptivo."""
    
    def test_alta_anticonceptivo_creation(self):
        """Test creación de alta con anticonceptivo."""
        alta = AltaAnticonceptivo.objects.create(
            fk_evento=1,
            tipo_alta='parto',
            fk_metodo_anticonceptivo='1',
            esterilizacion_quirurgica=False
        )
        self.assertEqual(alta.tipo_alta, 'parto')
        self.assertEqual(alta.fk_metodo_anticonceptivo, '1')
    
    def test_esterilizacion_quirurgica(self):
        """Test registro de esterilización quirúrgica."""
        alta = AltaAnticonceptivo.objects.create(
            fk_evento=2,
            tipo_alta='ive',
            esterilizacion_quirurgica=True
        )
        self.assertTrue(alta.esterilizacion_quirurgica)
