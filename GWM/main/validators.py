from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class NumericPasswordValidator:
    def validate(self, password, user=None):
        if not password.isdigit():
            raise ValidationError(
                _("A senha deve conter apenas números."),
                code='password_not_numeric',
            )

    def get_help_text(self):
        return _("Sua senha deve conter apenas números.")
