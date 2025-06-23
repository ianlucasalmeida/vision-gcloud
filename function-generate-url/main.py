import functions_framework
from google.cloud import storage
import datetime

# ATENÇÃO: Substitua pelo nome do seu bucket de uploads
BUCKET_NAME = "vision-gcloud-uploads" 

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada (Signed URL) para upload.
    Recebe um JSON com: {"fileName": "nome_do_arquivo.jpg"}
    """
    # --- Configuração de CORS para permitir requisições do navegador ---
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }

    # Trata a requisição pre-flight do navegador para CORS
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # --- Lógica Principal ---
    request_json = request.get_json(silent=True)
    if not request_json or 'fileName' not in request_json:
        return ('Requisição inválida. Faltando "fileName".', 400, headers)

    file_name = request_json['fileName']

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)

    # Gera a URL que será válida por 15 minutos para uma requisição PUT
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="PUT",
        content_type="application/octet-stream" 
    )

    # Retorna a URL como resposta
    return ({'url': signed_url}, 200, headers)