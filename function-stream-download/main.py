import functions_framework
from google.cloud import storage
import os
from flask import make_response

ALLOWED_ORIGINS = [
    'https://vision-gcloud.web.app',
    'https://vision-gcloud.firebaseapp.com'
]

@functions_framework.http
def stream_download_file(request):
    """
    Busca um arquivo privado no bucket e o transmite (streams)
    diretamente como uma resposta HTTP para forçar o download.
    """
    origin = request.headers.get('Origin')
    cors_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]

    headers = {
        'Access-Control-Allow-Origin': cors_origin,
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    file_name = request.args.get('file')
    if not file_name:
        return "Erro: Parâmetro 'file' não encontrado.", 400, headers

    try:
        storage_client = storage.Client()
        bucket_name = os.environ.get('PROCESSED_BUCKET_NAME')
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        if not blob.exists():
            return "Arquivo não encontrado.", 404, headers

        print(f"INFO: Entregando o arquivo '{file_name}' para download.")

        # Lê o conteúdo do arquivo
        file_data = blob.download_as_bytes()

        # Cria uma resposta HTTP
        response = make_response(file_data)
        # Define o tipo de conteúdo para que o navegador saiba o que fazer
        response.headers['Content-Type'] = blob.content_type
        # Força o navegador a tratar a resposta como um anexo para download
        response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'

        # Adiciona o cabeçalho de CORS à resposta final
        for key, value in headers.items():
            response.headers[key] = value

        return response

    except Exception as e:
        print(f"ERRO ao entregar o arquivo {file_name}: {e}")
        return "Erro interno ao processar o download.", 500, headers