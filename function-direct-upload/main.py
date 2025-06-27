import functions_framework
from google.cloud import storage
import os
import uuid
import time
import re
from werkzeug.utils import secure_filename

# Lista de origens permitidas
ALLOWED_ORIGINS = ['https://vision-gcloud.web.app', 'https://vision-gcloud.firebaseapp.com']
MAX_FILE_SIZE = 100 * 1024 * 1024

def generate_safe_filename(original_name):
    """Gera um nome de ficheiro único e seguro para evitar conflitos e caracteres inválidos."""
    # Separa o nome base da extensão
    name, ext = os.path.splitext(original_name)
    # Remove caracteres problemáticos e limita o tamanho do nome original
    sanitized_name = re.sub(r'[^\w.-]', '_', name)[:50]
    # Cria um identificador único com timestamp e um UUID curto
    unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    # Junta tudo num nome seguro e previsível
    return f"{sanitized_name}_{unique_id}{ext.lower()}"

@functions_framework.http
def direct_upload_file(request):
    """
    Recebe um ficheiro, gera um nome seguro para ele, salva-o no GCS
    e retorna o novo nome para o frontend.
    """
    origin = request.headers.get('Origin')
    cors_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    headers = {'Access-Control-Allow-Origin': cors_origin, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type'}
    
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    if 'file' not in request.files or 'action' not in request.form:
        return ('Requisição inválida. Faltando ficheiro ou ação.', 400, headers)

    file = request.files['file']
    action = request.form.get('action')
    
    # Gera o novo nome seguro para o ficheiro
    safe_filename = generate_safe_filename(file.filename)
    
    try:
        storage_client = storage.Client()
        bucket_name = os.environ.get('UPLOAD_BUCKET_NAME')
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(safe_filename)

        # Anexa a ação e o nome original como metadados para referência
        blob.metadata = {
            'action': action,
            'original_name': file.filename
        }
        
        # Adiciona parâmetros adicionais, se existirem
        if 'thumb_second' in request.form:
            blob.metadata['thumb_second'] = request.form.get('thumb_second')

        blob.upload_from_file(file.stream, content_type=file.content_type)
        
        print(f"SUCESSO: Ficheiro '{file.filename}' salvo como '{safe_filename}' com ação '{action}'.")
        
        # --- RESPOSTA ATUALIZADA ---
        # Devolve o nome seguro gerado para o frontend saber o que esperar
        return ({'status': 'success', 'savedFileName': safe_filename}, 200, headers)

    except Exception as e:
        print(f"ERRO CRÍTICO no upload: {e}")
        return ('Erro interno ao salvar o ficheiro.', 500, headers)
