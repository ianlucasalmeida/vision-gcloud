import functions_framework
from google.cloud import storage
import datetime
import os

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada (Signed URL) para upload.
    Esta é a versão final e corrigida.
    """
    headers = {
        'Access-Control-Allow-Origin': 'https://vision-gcloud.web.app',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
    if not bucket_name:
        return ('Erro de configuração no servidor: UPLOAD_BUCKET_NAME não definido.', 500, headers)

    request_json = request.get_json(silent=True)
    if not request_json or 'fileName' not in request_json:
        return ('Requisição inválida. O corpo da requisição deve ser um JSON com a chave "fileName".', 400, headers)

    file_name = request_json['fileName']
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        # --- CORREÇÃO FINAL ---
        # Removemos a necessidade de especificar o email da conta de serviço.
        # A biblioteca usará a permissão que já concedemos automaticamente.
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream"
        )
        return ({'url': signed_url}, 200, headers)
    except Exception as e:
        print(f"ERROR: Falha ao gerar a URL assinada: {e}")
        return (f'Erro interno ao gerar a URL.', 500, headers)