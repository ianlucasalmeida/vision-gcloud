import functions_framework
from google.cloud import storage
import datetime
import os

# Lista de origens permitidas para o seu site
ALLOWED_ORIGINS = [
    'https://vision-gcloud.web.app',
    'https://vision-gcloud.firebaseapp.com'
]

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada (Signed URL) para upload.
    Versão final e explícita.
    """
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        cors_origin = origin
    else:
        cors_origin = ALLOWED_ORIGINS[0] 

    headers = {
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # Lendo as configurações das variáveis de ambiente
    bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
    signing_sa_email = os.environ.get('SIGNING_SERVICE_ACCOUNT_EMAIL')

    if not bucket_name or not signing_sa_email:
        print("ERRO: Variáveis de ambiente UPLOAD_BUCKET_NAME ou SIGNING_SERVICE_ACCOUNT_EMAIL não configuradas.")
        return ('Erro de configuração interna no servidor.', 500, headers)

    request_json = request.get_json(silent=True)
    if not request_json or 'fileName' not in request_json:
        return ('Requisição inválida. O corpo da requisição deve ser um JSON com a chave "fileName".', 400, headers)

    file_name = request_json['fileName']
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream",
            service_account_email=signing_sa_email
        )
        return ({'url': signed_url}, 200, headers)
    except Exception as e:
        print(f"ERROR: Falha ao gerar a URL assinada: {e}")
        return ('Erro interno ao gerar a URL.', 500, headers)