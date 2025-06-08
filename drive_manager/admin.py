from django.contrib import admin
from .models import DownloadLog, PermissaoUsuario, PermissaoGrupo

@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_name', 'event_type', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__username', 'file_name')

@admin.register(PermissaoUsuario)
class PermissaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'acesso_civ', 'acesso_cipp', 'acesso_logs', 'pode_baixar')
    list_filter = ('acesso_civ', 'acesso_cipp', 'acesso_logs', 'pode_baixar')

@admin.register(PermissaoGrupo)
class PermissaoGrupoAdmin(admin.ModelAdmin):
    list_display = ('group', 'acesso_civ', 'acesso_cipp', 'acesso_logs', 'pode_baixar')
    list_filter = ('acesso_civ', 'acesso_cipp', 'acesso_logs', 'pode_baixar')
