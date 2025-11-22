print("--- CARGANDO COMANDO PERSONALIZADO ---")

from django.contrib.auth.management.commands.createsuperuser import Command as BaseCreateSuperUserCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError
from core.utils import validar_run
from core.models import Rol


class Command(BaseCreateSuperUserCommand):
    """
    Comando personalizado:
    - valida RUN en tiempo real y guarda el valor en self._last_run
    - lista roles y valida que el id sea entero y exista
    - intenta pasar fk_rol_id al crear el superusuario
    - si por alguna razón el usuario quedó creado sin fk_rol, lo actualiza después
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--fk_rol',
            dest='fk_rol',
            default=None,
            help='ID del rol asignado al superusuario',
        )

    # Guardamos el RUN ingresado en self._last_run para poder usarlo después
    def get_input_data(self, field, message, default=None):
        UserModel = get_user_model()
        username_field_name = getattr(UserModel, 'USERNAME_FIELD', 'username')
        field_name = getattr(field, 'name', field)

        # Si este input corresponde al campo username (run), validamos y lo guardamos
        if str(field_name) == str(username_field_name):
            while True:
                value = super().get_input_data(field, message, default)
                if value is None:
                    return value
                value = value.strip()

                if not validar_run(value):
                    self.stderr.write(self.style.ERROR("❌ RUN inválido. Intente nuevamente."))
                    continue

                # Guardamos para posterior uso (actualización en BD si hace falta)
                self._last_run = value
                return value

        return super().get_input_data(field, message, default)

    # Pedimos el rol y validamos su existencia antes de continuar
    def handle(self, *args, **options):

        # Si no viene por argumento --fk_rol, lo pedimos interactivo
        if not options.get("fk_rol"):
            print("\n📌 Roles disponibles:\n")

            roles = Rol.objects.all().order_by("id_rol")
            if not roles.exists():
                raise CommandError("❌ No existen roles en la base de datos. Cree roles primero.")

            for rol in roles:
                print(f"{rol.id_rol} → {rol}")  # __str__ de Rol

            while True:
                entrada = input("\nSeleccione el ID del rol: ").strip()

                # Validación: entero
                if not entrada.isdigit():
                    print("❌ Debe ingresar un número entero. Intente nuevamente.")
                    continue

                rol_id = int(entrada)

                # Validación: existe en BD
                if not Rol.objects.filter(id_rol=rol_id).exists():
                    print("❌ ID de rol no válido. Intente nuevamente.")
                    continue

                options["fk_rol"] = rol_id
                break

        # Intentamos pasar fk_rol al proceso normal de createsuperuser
        # Para lograrlo, agregamos fk_rol a options para que la lógica que
        # recolecta campos la tenga disponible como argumento CLI.
        # (Algunas versiones de Django sólo recogen USERNAME_FIELD y REQUIRED_FIELDS,
        #  así que hacemos un paso adicional: después de super().handle, si el usuario
        #  quedó creado sin fk_rol, lo actualizamos manualmente).
        fk_rol_provided = options.get("fk_rol")

        # Llamamos al handle original para que haga la recolección de campos y creación
        super().handle(*args, **options)

        # Si se pasó fk_rol y quedó guardado como NULL, intentamos actualizar el usuario creado
        if fk_rol_provided:
            UserModel = get_user_model()
            run = getattr(self, "_last_run", None)

            # Si el run lo tenemos (debido a la validación previa), intentamos buscar el usuario por run
            if run:
                try:
                    user = UserModel.objects.get(**{UserModel.USERNAME_FIELD: run})
                    # Si fk_rol es nulo o distinto, actualizamos
                    if getattr(user, "fk_rol_id", None) != int(fk_rol_provided):
                        user.fk_rol_id = int(fk_rol_provided)
                        user.save(update_fields=["fk_rol_id"])
                        self.stdout.write(self.style.SUCCESS(f"✅ fk_rol asignado correctamente al usuario {run}"))
                except UserModel.DoesNotExist:
                    # No se encontró usuario por run: nada que actualizar
                    self.stderr.write(self.style.WARNING(
                        f"⚠️ No se encontró usuario con {UserModel.USERNAME_FIELD}={run} para actualizar fk_rol."
                    ))
            else:
                # Si no tenemos run almacenado (caso raro), intentamos buscar por email si fue ingresado
                email = options.get("email")
                if email:
                    try:
                        user = UserModel.objects.get(email=email)
                        if getattr(user, "fk_rol_id", None) != int(fk_rol_provided):
                            user.fk_rol_id = int(fk_rol_provided)
                            user.save(update_fields=["fk_rol_id"])
                            self.stdout.write(self.style.SUCCESS(f"✅ fk_rol asignado correctamente al usuario con email {email}"))
                    except UserModel.DoesNotExist:
                        self.stderr.write(self.style.WARNING(
                            f"⚠️ No se encontró usuario con email={email} para actualizar fk_rol."
                        ))
