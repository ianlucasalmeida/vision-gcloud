import functions_framework
from google.cloud import storage
import datetime
import os  # Essencial para ler variáveis de ambiente

@functions_framework.http
def generate_upload_url(request):
    """
    Função HTTP que gera uma URL assinada (Signed URL) para upload.
    Esta é a versão final e corrigida.
    """
    # Configuração de CORS para permitir requisições do seu site no Firebase
    headers = {
        'Access-Control-Allow-Origin': 'https://vision-gcloud.web.app',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    # Responde à requisição 'OPTIONS' (pre-flight) do navegador
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # Lendo o nome do bucket da variável de ambiente
    bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
    if not bucket_name:
        # Em caso de erro, retorna a mensagem e os headers de CORS
        return ('Erro de configuração no servidor: UPLOAD_BUCKET_NAME não definido.', 500, headers)

    # Pega os dados JSON da requisição
    request_json = request.get_json(silent=True)
    if not request_json or 'fileName' not in request_json:
        return ('Requisição inválida. O corpo da requisição deve ser um JSON com a chave "fileName".', 400, headers)

    file_name = request_json['fileName']

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        # Pega o email da conta de serviço que está executando esta função.
        # O Google Cloud injeta esta variável de ambiente automaticamente.
        service_account_email = os.environ.get('FUNCTIONS_SERVICE_ACCOUNT')
        if not service_account_email:
             return ('Erro de configuração no servidor: Não foi possível determinar a conta de serviço da função.', 500, headers)

        # Gera a URL de upload segura e temporária
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream",
            # --- CORREÇÃO FINAL E CRUCIAL ---
            # Especifica qual conta de serviço deve ser usada para a assinatura,
            # utilizando a permissão de "Criador de token da conta de serviço" que concedemos.
            service_account_email=service_account_email
        )
        # Retorna a URL em um formato JSON com os headers de CORS
        return ({'url': signed_url}, 200, headers)

    except Exception as e:
        # Imprime o erro detalhado nos logs para depuração
        print(f"ERROR: Falha ao gerar a URL assinada: {e}")
        # Retorna uma mensagem de erro genérica com os headers de CORS
        return ('Erro interno ao gerar a URL.', 500, headers)