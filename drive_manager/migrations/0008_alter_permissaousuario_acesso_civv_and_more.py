# Generated by Django 4.2 on 2025-05-12 06:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('drive_manager', '0007_rename_acesso_consulta_permissaousuario_acesso_civv_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permissaousuario',
            name='acesso_civv',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='permissaousuario',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='permissousuario', to=settings.AUTH_USER_MODEL),
        ),
    ]
