# drive_manager/forms.py
from django import forms
from .models import PermissaoUsuario, PermissaoGrupo

class PermissaoUsuarioForm(forms.ModelForm):
    class Meta:
        model = PermissaoUsuario
        fields = ['acesso_civ', 'acesso_cipp', 'pode_baixar', 'acesso_logs']
        labels = {
            'acesso_civ': 'Acesso à CIV',
            'acesso_cipp': 'Acesso à CIPP',
            'pode_baixar': 'Pode baixar vídeos',
            'acesso_logs': 'Pode ver logs',
        }


class PermissaoGrupoForm(forms.ModelForm):
    class Meta:
        model = PermissaoGrupo
        fields = ['acesso_civ', 'acesso_cipp', 'pode_baixar', 'acesso_logs']
        labels = {
            'acesso_civ': 'Acesso à CIV',
            'acesso_cipp': 'Acesso à CIPP',
            'pode_baixar': 'Pode baixar vídeos',
            'acesso_logs': 'Pode ver logs',
        }
