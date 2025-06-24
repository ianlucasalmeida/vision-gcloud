import functions_framework
from google.cloud import storage
import datetime
import os

ALLOWED_ORIGINS = [
    'https://vision-gcloud.web.app',
    'https://vision-gcloud.firebaseapp.com',
    'http://localhost:8000'
]

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada (Signed URL) V4 para upload.
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

    bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
    # O email da conta de serviço que tem a permissão para assinar
    signing_sa_email = os.environ.get('SIGNING_SERVICE_ACCOUNT_EMAIL')

    if not bucket_name or not signing_sa_email:
        print("ERRO: Variáveis de ambiente não configuradas.")
        return ('Erro de configuração interna no servidor.', 500, headers)

    request_json = request.get_json(silent=True)
    if not request_json or 'fileName' not in request_json:
        return ('Requisição inválida.', 400, headers)

    file_name = request_json['fileName']
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        # --- CORREÇÃO FINAL E DEFINITIVA ---
        # Em vez de a função assinar, pedimos ao Google para assinar
        # usando a identidade da conta de serviço especificada.
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream",
            # O Google usará a API IAM Credentials para assinar em nome desta conta.
            # Isso requer que a conta que executa a função (a padrão) tenha o papel
            # de "Criador de token da conta de serviço" na conta `signing_sa_email`.
            service_account_email=signing_sa_email,
            access_token=None # Força o uso do fluxo de assinatura do IAM
        )
        return ({'url': url}, 200, headers)
    except Exception as e:
        print(f"ERRO CRÍTICO ao gerar URL: {e}")
        return ('Erro interno ao gerar a URL.', 500, headers)