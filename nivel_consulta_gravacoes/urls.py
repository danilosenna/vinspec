from django.contrib import admin
from django.urls import path, include
from drive_manager.views import CustomTwoFactorSetupWizard, setup_complete_view
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', lambda request: redirect('dashboard') if request.user.is_authenticated else redirect('two_factor:login')),
    path('admin/', admin.site.urls),

    # Wizard 2FA e telas de conclusão (customizadas)
    path('account/two_factor/setup/', CustomTwoFactorSetupWizard.as_view(), name='setup'),
    path('account/two_factor/setup/complete/', setup_complete_view, name='setup_complete'),
    path('account/setup/success/', setup_complete_view, name='setup_success'),

    # Roteamento da lib two_factor (mantém login, profile etc)
    #path('', include(('two_factor.urls', 'two_factor'), namespace='two_factor')),
    path('', include(('nivel_consulta_gravacoes.my_two_factor_urls', 'two_factor'), namespace='two_factor')),



    # App principal
    path('app/', include('drive_manager.urls')),
]

from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
