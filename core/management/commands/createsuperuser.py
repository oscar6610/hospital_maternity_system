from django.contrib.auth.management.commands.createsuperuser import Command as BaseCreateSuperUserCommand
from django.contrib.auth import get_user_model
from core.utils import validar_run


class Command(BaseCreateSuperUserCommand):
    """Extiende el comando para validar el RUN al ingresarlo en el prompt."""

    def get_input_data(self, field, message, default=None):
        """Sobrescribe el input para validar el RUN inmediatamente.

        `field` puede ser un nombre (str) o un objeto Field; comparamos
        con el `USERNAME_FIELD` del modelo para identificar el campo.
        """
        UserModel = get_user_model()
        username_field_name = getattr(UserModel, 'USERNAME_FIELD', 'username')

        # Determinar nombre del campo (si es Field, usar .name)
        field_name = getattr(field, 'name', field)

        # Si este input corresponde al campo de usuario (run), validar
        if str(field_name) == str(username_field_name):
            while True:
                value = super().get_input_data(field, message, default)
                if value is None:
                    return value
                value = value.strip()
                if not validar_run(value):
                    self.stderr.write(self.style.ERROR("RUN inválido, ingréselo nuevamente."))
                    continue  # vuelve a pedir el RUN
                return value

        # Para otros campos usar comportamiento por defecto
        return super().get_input_data(field, message, default)
