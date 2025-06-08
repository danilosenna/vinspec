from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()

try:
    user = User.objects.get(username='danilosenna')
    TOTPDevice.objects.filter(user=user).delete()
    print("TOTP resetado com sucesso para o usuário: {user.username}")
except User.DoesNotExist:
    print("Usuário não encontrado.")
