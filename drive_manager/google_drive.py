import os
import subprocess
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Caminho para o arquivo JSON da conta de serviço
SERVICE_ACCOUNT_FILE = "C:/Desenvolvimento/projeto_nivel_gravacoes/chave_api.json"

# Escopo para acesso ao Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# Autenticação e construção do serviço da API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)

# IDs das pastas específicas no Google Drive
FOLDER_ID_CIV = '1ZQXDbOv2wqeBphFNgWBVR0CPkhkEDyNI'
FOLDER_ID_CIPP = '1MfLD5WcuIEOIfCsHHUHrAd38cYKI8yGc'  # Ajuste conforme necessário

def listar_arquivos(folder_id=None):
    """
    Retorna a lista de arquivos presentes na pasta configurada ou na fornecida via argumento.
    """
    query = f"'{folder_id}' in parents and trashed=false"
    try:
        results = drive_service.files().list(q=query, fields="files(id, name, mimeType, size)").execute()
        return results.get('files', [])
    except HttpError as error:
        print(f"[ERRO] listar_arquivos: {error}")
        return []

def download_arquivo(file_id):
    """
    Faz o download do arquivo binário diretamente do Google Drive e retorna como bytes.
    """
    try:
        request = drive_service.files().get_media(fileId=file_id)
        return request.execute()  # Retorna os bytes do arquivo
    except HttpError as error:
        print(f"[ERRO] download_arquivo: {error}")
        return b''

def listar_itens_recursivamente(parent_id):
    """
    Lista itens de uma pasta (arquivos e subpastas) de forma recursiva.
    Retorna uma lista de dicionários que representam a estrutura hierárquica.
    """
    query = f"'{parent_id}' in parents and trashed=false"
    try:
        results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])
    except HttpError as error:
        print(f"[ERRO] listar_itens_recursivamente: {error}")
        items = []

    estrutura = []
    for item in items:
        if item.get('mimeType') == 'application/vnd.google-apps.folder':
            sub_itens = listar_itens_recursivamente(item['id'])
            estrutura.append({
                'id': item['id'],
                'name': item['name'],
                'mimeType': item['mimeType'],
                'itens': sub_itens
            })
        else:
            estrutura.append(item)
    return estrutura

def get_file_metadata(file_id):
    """
    Recupera os metadados do arquivo, incluindo o nome e o mimeType.
    """
    try:
        return drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
    except HttpError as error:
        print(f"[ERRO] get_file_metadata: {error}")
        return {}
