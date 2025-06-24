import os
from google.cloud import storage
from PIL import Image
# Importe outras bibliotecas de conversão aqui quando for expandir
# from docx2pdf import convert
# import ffmpeg

storage_client = storage.Client()

def vision_gcloud_processor(event, context):
    """
    Função acionada por um evento de upload no Cloud Storage.
    Processa o arquivo e o salva como PRIVADO no bucket de destino.
    """
    bucket_name = event['bucket']
    file_name = event['name']
    print(f"INFO: Novo arquivo '{file_name}' no bucket '{bucket_name}'.")

    source_bucket = storage_client.bucket(bucket_name)
    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = storage_client.bucket(destination_bucket_name)

    source_blob = source_bucket.blob(file_name)
    temp_file_path = f"/tmp/{os.path.basename(file_name)}"
    source_blob.download_to_filename(temp_file_path)
    
    processed_file_path = None
    processed_file_name = None

    try:
        # --- Lógica de Roteamento (pode ser expandida como antes) ---
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            processed_file_name = f"bw_{base_name}.jpg"
            processed_file_path = f"/tmp/{processed_file_name}"
            with Image.open(temp_file_path) as img:
                img.convert('L').save(processed_file_path, 'JPEG')
            print(f"INFO: Imagem convertida para preto e branco.")
        else:
            print(f"AVISO: Tipo de arquivo não suportado: '{file_name}'.")
            os.remove(temp_file_path)
            return

        # --- Upload do Resultado (como arquivo privado) ---
        if processed_file_path and processed_file_name:
            destination_blob = destination_bucket.blob(processed_file_name)
            destination_blob.upload_from_filename(processed_file_path)
            # A linha .make_public() foi REMOVIDA. O arquivo permanecerá privado.
            print(f"SUCESSO: Arquivo privado '{processed_file_name}' salvo em '{destination_bucket_name}'.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if processed_file_path and os.path.exists(processed_file_path):
            os.remove(processed_file_path)