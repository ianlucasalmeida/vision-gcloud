import functions_framework
from google.cloud import storage
import datetime
import os
import traceback # Importa a biblioteca para capturar o traceback completo

ALLOWED_ORIGINS = [
    'https://vision-gcloud.web.app',
    'https://vision-gcloud.firebaseapp.com'
]

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada - VERSÃO DE DEPURAÇÃO
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

    try:
        bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
        signing_sa_email = os.environ.get('SIGNING_SERVICE_ACCOUNT_EMAIL')

        if not bucket_name or not signing_sa_email:
            raise ValueError("Variáveis de ambiente não configuradas no servidor.")

        request_json = request.get_json(silent=True)
        if not request_json or 'fileName' not in request_json:
            raise ValueError("Requisição inválida, 'fileName' não encontrado.")

        file_name = request_json['fileName']
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream",
            service_account_email=signing_sa_email,
            access_token=None 
        )
        return ({'url': signed_url}, 200, headers)
        
    except Exception as e:
        # --- MUDANÇA CRUCIAL PARA DEPURAÇÃO ---
        # Captura o traceback completo do erro como uma string
        error_traceback = traceback.format_exc()
        # Imprime nos logs do servidor (boa prática)
        print(f"ERRO DETALHADO: {error_traceback}")
        # Retorna o traceback no corpo da resposta para o frontend
        return ({'error': str(e), 'traceback': error_traceback}, 500, headers)