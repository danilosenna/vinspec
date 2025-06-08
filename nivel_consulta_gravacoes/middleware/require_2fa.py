from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class Require2FAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        user = request.user

        # Ignora verificação se o usuário ainda não estiver autenticado
        if not user.is_authenticated:
            return self.get_response(request)

        # Rotas que não devem ser interceptadas
        exempt_paths = [
            '/account/login/',
            '/account/two_factor/setup/',
            '/account/two_factor/setup/complete/',
            '/account/two_factor/backup/tokens/',
            '/account/two_factor/disable/',
            '/account/two_factor/',
            '/logout/',
        ]

        if any(path.startswith(p) for p in exempt_paths):
            return self.get_response(request)

        # Verifica se o usuário já tem 2FA configurado
        is_verified = getattr(user, 'is_verified', lambda: False)()
        if not is_verified:
            if not request.session.get("two_factor_prompted", False):
                messages.warning(
                    request,
                    "Verificação em Duas Etapas não cadastrada. Você será redirecionado para a configuração."
                )
                request.session["two_factor_prompted"] = True
            return redirect(reverse('two_factor:setup'))

        return self.get_response(request)