# drive_manager/models.py
from django.db import models
from django.contrib.auth.models import User, Group


class DownloadLog(models.Model):
    EVENT_CHOICES = [
        ('Acesso', 'Acesso'),
        ('Visualização', 'Visualização'),
        ('Download', 'Download'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file_id = models.CharField(max_length=255, blank=True)
    file_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} – {self.event_type}: {self.file_name} em {self.timestamp:%d/%m/%Y %H:%M}'


class PermissaoUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="permissousuario")
    acesso_civ = models.BooleanField(default=False)
    acesso_cipp = models.BooleanField(default=False)
    acesso_logs = models.BooleanField(default=False)
    pode_baixar = models.BooleanField(default=True)

    def __str__(self):
        return f"Permissões de {self.user.username}"


class PermissaoGrupo(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    acesso_civ = models.BooleanField(default=True)
    acesso_cipp = models.BooleanField(default=True)
    pode_baixar = models.BooleanField(default=True)
    acesso_logs = models.BooleanField(default=False)

    def __str__(self):
        return f"Permissões do grupo {self.group.name}"
