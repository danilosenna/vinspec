from django.urls import path
from two_factor.views import LoginView
from two_factor.urls import urlpatterns as base_urlpatterns
from django.urls.resolvers import URLPattern, URLResolver

# Registra manualmente a view de login com nome 'login'
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
]

# Adiciona as demais rotas padrão
urlpatterns += [p for p in base_urlpatterns if isinstance(p, (URLPattern, URLResolver))]
