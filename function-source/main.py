import os
from google.cloud import storage
from PIL import Image

# Inicializa o cliente do Cloud Storage.
# Fora da função para que possa ser reutilizado entre invocações (melhor prática).
storage_client = storage.Client()

def vision_gcloud_processor(event, context):
    """
    Função serverless acionada por um upload no Cloud Storage.
    Converte a imagem enviada para preto e branco.
    """
    # Obtém o nome do bucket e do arquivo a partir do evento de gatilho.
    bucket_name = event['bucket']
    file_name = event['name']

    print(f"INFO: Processamento iniciado para o arquivo {file_name} do bucket {bucket_name}.")

    # Define os buckets de origem e destino.
    source_bucket = storage_client.bucket(bucket_name)

    # O nome do bucket de destino será lido de uma variável de ambiente.
    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = storage_client.bucket(destination_bucket_name)

    # Representa o objeto (arquivo) que foi enviado.
    source_blob = source_bucket.blob(file_name)

    # Baixa o arquivo para um diretório temporário no ambiente da função.
    # O Cloud Functions só permite escrever na pasta /tmp.
    temp_file_path = f"/tmp/{os.path.basename(file_name)}"
    source_blob.download_to_filename(temp_file_path)

    print(f"INFO: Arquivo {file_name} baixado para o ambiente temporário.")

    # Bloco Try/Finally para garantir que os arquivos temporários sejam sempre limpos.
    try:
        # --- LÓGICA DE PROCESSAMENTO ---
        print(f"INFO: Iniciando conversão da imagem para preto e branco.")

        processed_file_name = f"bw_{os.path.basename(file_name)}"
        temp_processed_path = f"/tmp/{processed_file_name}"

        # Abre a imagem, converte para 'L' (Luminance/Preto e Branco) e salva.
        with Image.open(temp_file_path) as img:
            img.convert('L').save(temp_processed_path)

        print(f"INFO: Imagem convertida com sucesso.")

        # --- UPLOAD DO RESULTADO ---
        # Cria um novo blob (objeto) no bucket de destino e faz o upload.
        destination_blob = destination_bucket.blob(processed_file_name)
        destination_blob.upload_from_filename(temp_processed_path)

        print(f"SUCESSO: Arquivo {processed_file_name} salvo no bucket {destination_bucket_name}.")

    except Exception as e:
        print(f"ERRO: Falha no processamento. Motivo: {e}")
    finally:
        # --- LIMPEZA ---
        # Remove os arquivos temporários do sistema de arquivos da função.
        os.remove(temp_file_path)
        if 'temp_processed_path' in locals() and os.path.exists(temp_processed_path):
            os.remove(temp_processed_path)
        print("INFO: Limpeza dos arquivos temporários concluída.")