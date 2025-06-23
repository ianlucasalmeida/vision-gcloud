import os
from google.cloud import storage
from PIL import Image

# Para futuras expansões, você importará outras bibliotecas aqui
# from docx2pdf import convert 

storage_client = storage.Client()

def vision_gcloud_processor(event, context):
    """
    Função acionada por um evento de upload no Cloud Storage.
    Processa o arquivo baseado na sua extensão.
    """
    bucket_name = event['bucket']
    file_name = event['name']

    print(f"INFO: Novo arquivo '{file_name}' no bucket '{bucket_name}'. Iniciando processamento.")

    source_bucket = storage_client.bucket(bucket_name)
    
    # Lê o nome do bucket de destino da variável de ambiente
    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = storage_client.bucket(destination_bucket_name)

    source_blob = source_bucket.blob(file_name)
    temp_file_path = f"/tmp/{os.path.basename(file_name)}"
    source_blob.download_to_filename(temp_file_path)
    
    processed_file_path = None
    processed_file_name = None

    try:
        # --- Roteador de Processamento ---
        # Verifica a extensão do arquivo e direciona para a lógica correta.

        # LÓGICA EXISTENTE PARA IMAGENS
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"INFO: Roteado para processador de imagens.")
            processed_file_name = f"bw_{os.path.basename(file_name)}"
            processed_file_path = f"/tmp/{processed_file_name}"
            with Image.open(temp_file_path) as img:
                img.convert('L').save(processed_file_path)
            print(f"INFO: Imagem convertida para preto e branco.")

        # Exemplo de como você adicionaria a conversão de DOCX (descomente quando for implementar)
        # elif file_name.lower().endswith('.docx'):
        #     print(f"INFO: Roteado para processador de DOCX.")
        #     base_name = os.path.splitext(os.path.basename(file_name))[0]
        #     processed_file_name = f"{base_name}.pdf"
        #     processed_file_path = f"/tmp/{processed_file_name}"
        #     convert(temp_file_path, processed_file_path)
        #     print(f"INFO: Arquivo .docx convertido para .pdf.")

        else:
            print(f"AVISO: Nenhuma ação definida para o tipo de arquivo '{file_name}'.")
            os.remove(temp_file_path)
            return

        # --- Upload do Resultado ---
        if processed_file_path and processed_file_name:
            destination_blob = destination_bucket.blob(processed_file_name)
            destination_blob.upload_from_filename(processed_file_path)
            destination_blob.make_public() # Torna o arquivo acessível para download
            print(f"SUCESSO: Arquivo '{processed_file_name}' salvo em '{destination_bucket_name}'.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento: {e}")
    finally:
        # Limpeza segura dos arquivos temporários
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if processed_file_path and os.path.exists(processed_file_path):
            os.remove(processed_file_path)
        print("INFO: Limpeza de arquivos temporários concluída.")