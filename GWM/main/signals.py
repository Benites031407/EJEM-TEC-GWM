# main/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def ao_logar(sender, request, user, **kwargs):
    if user.cge and user.check_password(user.cge):
        request.session['exibir_popup_primeiro_login'] = True
    else:
        request.session['exibir_popup_primeiro_login'] = False

