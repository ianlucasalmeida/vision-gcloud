import functions_framework
from google.cloud import storage
import datetime
import os
from flask import redirect

@functions_framework.http
def generate_download_url(request):
    """
    Função HTTP que gera uma URL assinada para DOWNLOAD e redireciona o usuário.
    Recebe o nome do arquivo como um parâmetro de URL. Ex: ?file=meu_arquivo.jpg
    """
    file_name = request.args.get('file')
    if not file_name:
        return "Erro: O nome do arquivo (parâmetro 'file') é necessário.", 400

    storage_client = storage.Client()
    # Lê o nome do bucket de arquivos processados de uma variável de ambiente
    bucket_name = os.environ.get('PROCESSED_BUCKET_NAME')
    signing_sa_email = os.environ.get('SIGNING_SERVICE_ACCOUNT_EMAIL')

    if not bucket_name or not signing_sa_email:
        print("ERRO: Variáveis de ambiente não configuradas.")
        return ('Erro de configuração interna no servidor.', 500)
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    if not blob.exists():
        return "Arquivo não encontrado no armazenamento.", 404

    try:
        # Gera uma URL assinada válida por 5 minutos para download (GET)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=5),
            method="GET",
            service_account_email=signing_sa_email,
            access_token=None
        )
        # Redireciona o navegador do usuário para a URL de download, iniciando-o
        return redirect(signed_url)
    except Exception as e:
        print(f"ERRO ao gerar URL de download para {file_name}: {e}")
        return "Erro ao gerar link de download.", 500