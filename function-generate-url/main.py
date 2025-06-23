import functions_framework
from google.cloud import storage
import datetime
import os

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada (Signed URL) para upload.
    """
    # --- CORREÇÃO DE CORS ---
    # A origem agora é a URL exata do seu site no Firebase Hosting.
    headers = {
        'Access-Control-Allow-Origin': 'https://vision-gcloud.web.app',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    # Responde à requisição 'OPTIONS' do navegador para verificação de CORS
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # --- Lógica Principal ---
    # Lendo o nome do bucket da variável de ambiente para mais segurança
    bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
    if not bucket_name:
        return ('Variável de ambiente UPLOAD_BUCKET_NAME não configurada.', 500, headers)

    request_json = request.get_json(silent=True)
    if not request_json or 'fileName' not in request_json:
        return ('Requisição inválida. Faltando "fileName".', 400, headers)

    file_name = request_json['fileName']
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        # Gera a URL de upload segura e temporária
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream" 
        )
        return ({'url': signed_url}, 200, headers)
    except Exception as e:
        return (f'Erro interno: {e}', 500, headers)