import functions_framework
from google.cloud import storage
import os
from werkzeug.utils import secure_filename

# Lista de origens permitidas
ALLOWED_ORIGINS = [
    'https://vision-gcloud.web.app',
    'https://vision-gcloud.firebaseapp.com'
]

@functions_framework.http
def http_upload_file(request):
    """
    Função HTTP que recebe um arquivo via POST e o salva no Cloud Storage.
    """
    origin = request.headers.get('Origin')
    cors_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]

    headers = {
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # Verifica se um arquivo foi enviado na requisição
    if 'file' not in request.files:
        return ('Nenhum arquivo enviado.', 400, headers)

    file = request.files['file']

    if file.filename == '':
        return ('Nome de arquivo vazio.', 400, headers)

    # Usa o nome do arquivo original de forma segura
    filename = secure_filename(file.filename)

    try:
        storage_client = storage.Client()
        bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)

        print(f"INFO: Recebendo o arquivo '{filename}' para salvar no bucket '{bucket_name}'.")

        # Faz o upload do stream do arquivo para o bucket
        blob.upload_from_file(file.stream, content_type=file.content_type)

        print(f"SUCESSO: Arquivo '{filename}' salvo com sucesso.")

        return ({'status': 'success', 'fileName': filename}, 200, headers)

    except Exception as e:
        print(f"ERRO CRÍTICO no upload: {e}")
        return ('Erro interno ao salvar o arquivo.', 500, headers)