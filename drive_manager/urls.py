from django.urls import path
from . import views
from two_factor.views import LoginView  # ← LoginView da 2FA

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('consulta_inspecoes_civ/', views.consulta_inspecoes_civ, name='consulta_inspecoes_civ'),
    path('consulta_inspecoes_cipp/', views.consulta_inspecoes_cipp, name='consulta_inspecoes_cipp'),
    path('visualizar/<str:file_id>/', views.visualizar_arquivo, name='visualizar_arquivo'),
    path('baixar/<str:file_id>/', views.baixar_arquivo, name='baixar_arquivo'),
    path('registro_logs/', views.listar_logs, name='listar_logs'),
    path('configuracoes/', views.configurar_permissoes, name='configurar_permissoes'),
    path('account/login/', LoginView.as_view(), name='login'),
    path('consulta_fotos/', views.consulta_fotos, name='consulta_fotos'),
    path('visualizar_foto/<str:file_id>/', views.visualizar_foto, name='visualizar_foto'),
    path('baixar_foto/<str:file_id>/', views.baixar_foto, name='baixar_foto'),
    path('registrar_visualizacao_ajax/', views.registrar_visualizacao_ajax, name='registrar_visualizacao_ajax'),


    # 🔁 Logout personalizado
    path('account/logout/', views.logout_customizado, name='logout'),
]
