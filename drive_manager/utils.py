# drive_manager/utils.py

import os
import subprocess
from django.conf import settings

def converter_dav_para_mp4(input_path, output_filename):
    """
    Converte um arquivo .dav para .mp4 usando ffmpeg.
    - Se já existir o .mp4, retorna o caminho sem reconverter.
    - Se converter com sucesso, remove o .dav temporário.
    Retorna o caminho do .mp4 gerado ou None em caso de falha.
    """
    # diretório onde ficam os .mp4 convertidos
    output_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    # se já existe, limpa o temp (.dav) e retorna
    if os.path.exists(output_path):
        try:
            os.remove(input_path)
        except OSError:
            pass
        return output_path

    # faz a conversão
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path
        ], check=True)

        if os.path.exists(output_path):
            # remove o .dav temporário
            try:
                os.remove(input_path)
            except OSError:
                pass
            return output_path

    except subprocess.CalledProcessError:
        # conversão falhou
        pass

    return None

def extrair_resolucao_mp4(path_arquivo):
    try:
        comando = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            path_arquivo
        ]
        resultado = subprocess.check_output(comando).decode().split()
        if len(resultado) >= 2:
            largura, altura = resultado[:2]
            return f"{largura}x{altura}"
    except Exception:
        pass
    return '--'
