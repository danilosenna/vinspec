from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.conf import settings
from django_otp import devices_for_user
from django_otp.decorators import otp_required
from functools import wraps
import datetime, re, os, csv
from collections import defaultdict
from django.utils.html import format_html

from .models import PermissaoUsuario, PermissaoGrupo, DownloadLog
from .forms import PermissaoUsuarioForm
from .google_drive import listar_arquivos, download_arquivo, get_file_metadata
from .google_drive import FOLDER_ID_CIV, FOLDER_ID_CIPP
import json


CERTIFICADOS_POR_PAGINA = 20

# Decorator de 2FA inteligente
def otp_if_configured_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if any(dev.confirmed for dev in devices_for_user(request.user)):
            return otp_required(view_func)(request, *args, **kwargs)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Helpers
def get_file_info(filename: str):
    try:
        name = os.path.splitext(filename)[0]
        parts = name.split('_')
        camera = f"Câmera {int(parts[0][2:])}" if parts[0].startswith('ch') else parts[0]

        # Converte data no padrão DDMMYYYYHHMMSS para datetime
        def parse_dt(val):
            try:
                return datetime.datetime.strptime(val, "%Y%m%d%H%M%S")  # padrão antigo
            except:
                return datetime.datetime.strptime(val, "%d%m%Y%H%M%S")  # novo formato

        dt_ini = parse_dt(parts[2])
        dt_fim = parse_dt(parts[3])

        return {
            'camera': camera,
            'data': dt_ini.strftime("%d/%m/%Y"),
            'hora_inicio': dt_ini.strftime("%H:%M"),
            'hora_fim': dt_fim.strftime("%H:%M"),
            'friendly_name': f"{camera} - Dia {dt_ini.strftime('%d-%m-%Y')} das {dt_ini.strftime('%H:%M')}h às {dt_fim.strftime('%H:%M')}h"
        }

    except Exception:
        return {
            'camera': '--',
            'data': '--',
            'hora_inicio': '--',
            'hora_fim': '--',
            'friendly_name': filename
        }

import datetime
import os

def get_info_foto(nome_arquivo: str):
    try:
        base = os.path.splitext(nome_arquivo)[0].replace('_thumbnail', '')
        partes = base.split('-')

        tipo = partes[1].upper() if len(partes) > 1 else '--'
        timestamp_str = partes[2] if len(partes) > 2 else ''
        data_str = timestamp_str[:8]
        hora_str = timestamp_str[9:15]
        numero_certificado = timestamp_str[-4:]  # Últimos 4 dígitos como número do certificado

        if len(data_str) != 8 or len(hora_str) != 6:
            raise ValueError("Formato inválido para data ou hora.")

        data_obj = datetime.datetime.strptime(data_str + hora_str, "%Y%m%d%H%M%S")

        data_formatada = data_obj.strftime("%d/%m/%Y")
        hora_formatada = data_obj.strftime("%H:%M:%S")

        return {
            'tipo_certificado': tipo,
            'numero_certificado': numero_certificado,
            'data': data_obj,  # para ordenação no Python
            'hora': hora_formatada,
            'data_str': data_formatada,  # para exibição
            'friendly_name': f'{tipo} {numero_certificado} - {data_formatada} às {hora_formatada}'
        }

    except Exception as e:
        print(f"[get_info_foto] Erro ao processar: {nome_arquivo} – {e}")
        return {
            'tipo_certificado': '--',
            'numero_certificado': '--',
            'data': datetime.datetime.min,  # coloca no fim da ordenação
            'hora': '--',
            'data_str': '--',
            'friendly_name': nome_arquivo
        }


def formatar_tamanho(bytes_str):
    try:
        size = int(bytes_str)
        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.0f} {unidade}"
            size /= 1024
    except Exception:
        pass
    return '--'

def tem_acesso(user, tipo):
    if user.is_superuser:
        return True
    usuario = getattr(user, 'permissousuario', None)
    if usuario:
        if tipo == 'civ' and usuario.acesso_civ:
            return True
        if tipo == 'cipp' and usuario.acesso_cipp:
            return True
        if tipo == 'logs' and usuario.acesso_logs:
            return True
    for group in user.groups.all():
        grupo = getattr(group, 'permissaogrupo', None)
        if grupo:
            if tipo == 'civ' and grupo.acesso_civ:
                return True
            if tipo == 'cipp' and grupo.acesso_cipp:
                return True
            if tipo == 'logs' and grupo.acesso_logs:
                return True
    return False

def pode_baixar(user):
    if user.is_superuser:
        return True
    usuario = getattr(user, 'permissousuario', None)
    if usuario and usuario.pode_baixar:
        return True
    for group in user.groups.all():
        grupo = getattr(group, 'permissaogrupo', None)
        if grupo and grupo.pode_baixar:
            return True
    return False

# Views principais
@login_required
def dashboard(request):
    from django_otp.plugins.otp_totp.models import TOTPDevice
    if not TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
        return redirect('setup')
    return render(request, 'drive_manager/dashboard.html')


# ID da pasta de fotos (ajustar conforme sua estrutura)
FOLDER_ID_FOTOS = '13iTnluVpErstdLNp1NpP3tTmTYimahu9'

def extrair_dados_foto(nome_arquivo):
    try:
        # Remove extensão e "_thumbnail" se houver
        base = nome_arquivo.rsplit('.', 1)[0].replace('_thumbnail', '')
        partes = base.split('-')

        numero = partes[0].upper() if len(partes) > 0 else '--'
        tipo = partes[1].upper() if len(partes) > 1 else '--'
        data_hora = partes[2] if len(partes) > 2 else ''

        data_str = data_hora[:8]
        hora_str = data_hora[9:13] if len(data_hora) >= 13 else ''

        data_fmt = datetime.datetime.strptime(data_str, "%Y%m%d").strftime("%d/%m/%Y") if len(data_str) == 8 else '--'
        hora_fmt = f"{hora_str[:2]}:{hora_str[2:]}" if len(hora_str) == 4 else '--'

        return data_fmt, hora_fmt, numero, tipo
    except Exception:
        return '--', '--', '--', '--'

import datetime
def registrar_log(user, file_name, event_type, file_id=""):
    DownloadLog.objects.create(
        user=user,
        file_id=file_id,
        file_name=file_name,
        event_type=event_type
    )

@otp_required
def consulta_fotos(request):
    if not tem_acesso(request.user, 'civv'):
        return HttpResponseForbidden("Você não tem permissão para acessar esta área.")

    # Log de acesso à tela de fotos
    registrar_log(request.user, 'Acesso à consulta de fotos', 'Acesso')

    search = request.GET.get('search', '').lower()
    todos_arquivos = listar_arquivos(FOLDER_ID_FOTOS)
    grupos = defaultdict(list)

    for arq in todos_arquivos:
        nome = arq.get('name', '')
        if '_thumbnail' in nome.lower() or not nome.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            continue
        info = get_info_foto(nome)
        if search and search not in nome.lower() \
                and search not in info['numero_certificado'].lower() \
                and search not in info['tipo_certificado'].lower():
            continue
        arq.update({
            'data': info['data'],
            'hora': info['hora'],
            'numero_certificado': info['numero_certificado'],
            'tipo_certificado': info['tipo_certificado'],
            'friendly_name': info['friendly_name'],
            'pode_baixar': pode_baixar(request.user),
        })
        chave = f"{info['numero_certificado']}_{info['tipo_certificado']}"
        grupos[chave].append(arq)

    grupos_ordenados = sorted(grupos.items(), key=lambda x: x[1][0]['data'], reverse=True)

    paginator = Paginator(grupos_ordenados, CERTIFICADOS_POR_PAGINA)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    grupos_json = {
        chave: [{'id': a['id'], 'name': a['name']} for a in grupo]
        for chave, grupo in page_obj
    }

    return render(request, 'drive_manager/lista_fotos.html', {
        'grupos': page_obj,
        'search_query': search,
        'grupos_json': json.dumps(grupos_json),
        'page_obj': page_obj,
    })



@otp_required
def visualizar_foto(request, file_id):
    origem = request.GET.get('origem', 'consulta_fotos')
    meta = get_file_metadata(file_id)
    nome = meta.get('name', '')

    if not nome.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
        return HttpResponse("Formato não suportado para visualização.")

    # Registra visualização corretamente
    registrar_log(request.user, nome, 'Visualização', file_id)

    file_url = f"https://drive.google.com/file/d/{file_id}/preview"

    return render(request, 'drive_manager/player_foto.html', {
        'file_url': file_url,
        'file_id': file_id,
        'file_name': nome,
        'origem': origem,
        'pode_baixar': pode_baixar(request.user),
    })


@otp_required
def baixar_foto(request, file_id):
    if not pode_baixar(request.user):
        return HttpResponseForbidden("Você não tem permissão para baixar arquivos.")

    meta = get_file_metadata(file_id)
    nome = meta.get('name', 'arquivo')

    DownloadLog.objects.create(
        user=request.user,
        file_id=file_id,
        file_name=nome,
        event_type='Download'
    )

    conteudo = download_arquivo(file_id)

    return HttpResponse(
        conteudo,
        content_type='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{nome}"'}
    )



@otp_required
def consulta_inspecoes_civ(request):
    if not tem_acesso(request.user, 'civ'):
        return HttpResponseForbidden("Acesso à CIV não autorizado.")
    return _consulta_arquivos(request, FOLDER_ID_CIV, "CIV")

@otp_required
def consulta_inspecoes_cipp(request):
    if not tem_acesso(request.user, 'cipp'):
        return HttpResponseForbidden("Acesso à CIPP não autorizado.")
    return _consulta_arquivos(request, FOLDER_ID_CIPP, "CIPP")

@otp_required
def _consulta_arquivos(request, folder_id, nome_consulta):
    DownloadLog.objects.create(
        user=request.user,
        file_id='',
        file_name=f"Acesso à consulta de inspeções {nome_consulta}",
        event_type='Acesso'
    )
    search = request.GET.get('search', '').strip().lower()
    todos_arquivos = listar_arquivos(folder_id)
    arquivos = [a for a in todos_arquivos if a.get('mimeType') != "application/vnd.google-apps.folder" and a.get('name', '').lower().endswith('.mp4')]
    for a in arquivos:
        info = get_file_info(a['name'])
        a.update(info)
        a['size_fmt'] = formatar_tamanho(a.get('size', ''))
        a['resolucao'] = '--'
    if search:
        arquivos = [a for a in arquivos if search in a['name'].lower() or search in a['camera'].lower() or search in a['data'].lower() or search in a['hora_inicio'].lower() or search in a['hora_fim'].lower() or search in a['friendly_name'].lower()]
    arquivos.sort(key=lambda x: datetime.datetime.strptime(f"{x['data']} {x['hora_inicio']}", "%d/%m/%Y %H:%M"),
    reverse=True
)
    pag = Paginator(arquivos, 50)
    page = request.GET.get('page')
    page_obj = pag.get_page(page)
    return render(request, 'drive_manager/lista_arquivos.html', {
        'arquivos': page_obj,
        'search_query': search,
        'parent_id': None,
        'folder': folder_id,
        'consulta_label': nome_consulta,
        'pode_baixar': pode_baixar(request.user),
    })


@otp_required
def visualizar_arquivo(request, file_id):
    origem = request.GET.get('origem', 'consulta_inspecoes_civ')
    if origem not in ['consulta_inspecoes_civ', 'consulta_inspecoes_cipp']:
        origem = 'consulta_inspecoes_civ'
    meta = get_file_metadata(file_id)
    nome = meta.get('name', '')
    if not nome.lower().endswith('.mp4'):
        raise HttpResponse("Formato não suportado para visualização.")
    DownloadLog.objects.create(user=request.user, file_id=file_id, file_name=nome, event_type='Visualização')
    video_url = f"https://drive.google.com/file/d/{file_id}/preview"
    return render(request, 'drive_manager/player.html', {
        'video_url': video_url,
        'file_id': file_id,
        'origem': origem,
        'pode_baixar': pode_baixar(request.user),
    })

@otp_required
def baixar_arquivo(request, file_id):
    if not pode_baixar(request.user):
        return HttpResponseForbidden("Você não tem permissão para baixar arquivos.")
    meta = get_file_metadata(file_id)
    nome = meta.get('name', 'arquivo')
    DownloadLog.objects.create(user=request.user, file_id=file_id, file_name=nome, event_type='Download')
    conteudo = download_arquivo(file_id)
    return HttpResponse(
        conteudo,
        content_type='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{nome}"'}
    )


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
@login_required
def registrar_visualizacao_ajax(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        file_name = request.POST.get('file_name')
        if file_id and file_name:
            registrar_log(request.user, file_name, 'Visualização', file_id)
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'erro', 'detalhe': 'faltando dados'}, status=400)
    return JsonResponse({'status': 'erro', 'detalhe': 'método inválido'}, status=405)


@otp_if_configured_required
def listar_logs(request):
    if not tem_acesso(request.user, 'logs'):
        return HttpResponseForbidden("Você não tem permissão para acessar os logs.")
    search = request.GET.get('search', '').strip()
    export = request.GET.get('export', '').strip().lower()
    qs = DownloadLog.objects.select_related('user').all().order_by('-timestamp')
    if search:
        q = (
            Q(user__username__icontains=search) |
            Q(file_name__icontains=search) |
            Q(event_type__icontains=search)
        )
        m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', search)
        if m:
            d, mo, y = m.groups()
            try:
                dt = datetime.date(int(y), int(mo), int(d))
                q |= Q(timestamp__date=dt)
            except ValueError:
                pass
        qs = qs.filter(q)
    total_acessos = qs.filter(event_type='Acesso').count()
    total_visualizacoes = qs.filter(event_type='Visualização').count()
    total_downloads = qs.filter(event_type='Download').count()
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['Usuário', 'Arquivo', 'Câmera', 'Data', 'Hora', 'Evento'])
        for log in qs:
            nome = log.file_name or ''
            parts = nome.lower().split('_')
            try:
                camera = f"Câmera {int(parts[0][2:])}" if parts[0].startswith('ch') else '--'
            except Exception:
                camera = '--'
            dt = log.timestamp.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))
            writer.writerow([
                log.user.username,
                nome,
                camera,
                dt.strftime('%d/%m/%Y'),
                dt.strftime('%H:%M:%S'),
                log.event_type
            ])
        return response
    pag = Paginator(qs, 100)
    page = request.GET.get('page')
    logs = pag.get_page(page)
    for log in logs:
        parts = log.file_name.lower().split('_')
        try:
            log.camera = f"Câmera {int(parts[0][2:])}" if parts[0].startswith('ch') else '--'
            dt = log.timestamp.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))
            log.data = dt.strftime('%d/%m/%Y')
            log.hora = dt.strftime('%H:%M:%S')
        except Exception:
            log.camera = '--'
            log.data = '--'
            log.hora = '--'
    return render(request, 'drive_manager/logs.html', {
        'logs': logs,
        'search_query': search,
        'total_acessos': total_acessos,
        'total_visualizacoes': total_visualizacoes,
        'total_downloads': total_downloads,
    })


@user_passes_test(lambda u: u.is_superuser)
def configurar_permissoes(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        perm, _ = PermissaoUsuario.objects.get_or_create(user=user)
        form = PermissaoUsuarioForm(request.POST, instance=perm)
        if form.is_valid():
            form.save()
            return redirect('configurar_permissoes')
    usuarios = []
    for user in User.objects.all().order_by('username'):
        perm, _ = PermissaoUsuario.objects.get_or_create(user=user)
        form = PermissaoUsuarioForm(instance=perm)
        usuarios.append({'usuario': user, 'form': form})
    return render(request, 'drive_manager/configurar_permissoes.html', {'usuarios': usuarios})


# ⚙️ Custom wizard 2FA
from formtools.wizard.views import SessionWizardView
from django import forms
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
import qrcode
import base64
from io import BytesIO

class GeneratorForm(forms.Form):
    token = forms.CharField(label='Código', max_length=6)

@method_decorator(login_required, name='dispatch')
class CustomTwoFactorSetupWizard(SessionWizardView):
    form_list = [('generator', GeneratorForm)]
    template_name = 'two_factor/setup.html'

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        device, _ = TOTPDevice.objects.get_or_create(user=self.request.user, name='default', confirmed=False)
        otp_uri = device.config_url
        qr = qrcode.make(otp_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        context['qr_base64'] = qr_base64
        return context

    def done(self, form_list, **kwargs):
        form = form_list[0]
        token = form.cleaned_data['token']
        user = self.request.user
        device = TOTPDevice.objects.filter(user=user, name='default').first()

        if device and device.verify_token(token):
            device.confirmed = True
            device.save()
            return redirect('setup_complete')

        form.add_error('token', 'Código inválido.')
        return self.render(self.get_form(step=self.steps.current))

def setup_complete_view(request):
    return render(request, 'two_factor/setup_complete.html')

from django.contrib.auth import logout
from django.shortcuts import render, redirect

def logout_customizado(request):
    logout(request)
    return render(request, 'registration/logged_out.html')