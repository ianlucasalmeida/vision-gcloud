import functions_framework
from google.cloud import storage
import os
from werkzeug.utils import secure_filename

ALLOWED_ORIGINS = ['https://vision-gcloud.web.app', 'https://vision-gcloud.firebaseapp.com']

@functions_framework.http
def direct_upload_file(request):
    origin = request.headers.get('Origin')
    cors_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    headers = {'Access-Control-Allow-Origin': cors_origin, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type'}
    
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    if 'file' not in request.files or 'action' not in request.form:
        return ('Requisição inválida. Faltando arquivo ou ação.', 400, headers)

    file = request.files['file']
    action = request.form.get('action')
    filename = secure_filename(file.filename)
    
    try:
        storage_client = storage.Client()
        bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)

        # --- MUDANÇA IMPORTANTE: Salva a ação como metadado ---
        blob.metadata = {'action': action}
        
        blob.upload_from_file(file.stream, content_type=file.content_type)
        
        print(f"SUCESSO: Arquivo '{filename}' com ação '{action}' salvo no bucket '{bucket_name}'.")
        return ({'status': 'success', 'fileName': filename}, 200, headers)

    except Exception as e:
        print(f"ERRO CRÍTICO no upload: {e}")
        return ('Erro interno ao salvar o arquivo.', 500, headers)
