import os
from google.cloud import storage
from PIL import Image
import pillow_heif

# Registra o suporte para o formato HEIF/HEIC (requer a biblioteca libheif no sistema)
pillow_heif.register_heif_opener()

def apply_sepia(img):
    """Aplica um filtro de sépia, garantindo que a imagem está em modo RGB."""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    # Matriz de cores para o filtro sépia
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    """
    Lê a ação dos metadados e processa ficheiros de imagem com lógica robusta.
    """
    file_data = event
    bucket_name = file_data['bucket']
    file_name = file_data['name']
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    
    # Validação inicial dos metadados
    if not blob or not blob.metadata or 'action' not in blob.metadata:
        print(f"AVISO: Ficheiro '{file_name}' recebido sem o metadado 'action'. Ignorando.")
        return

    action = blob.metadata['action']
    print(f"INFO: Ficheiro '{file_name}' recebido com ação '{action}'.")

    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = client.bucket(destination_bucket_name)

    temp_input_path = os.path.join('/tmp', os.path.basename(file_name))
    blob.download_to_filename(temp_input_path)
    
    processed_file_path = None
    
    try:
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        
        # --- ROTEADOR DE PROCESSAMENTO DE IMAGEM ---
        
        # Abre a imagem uma única vez
        img = Image.open(temp_input_path)

        # Trata a transparência (ex: em ficheiros .png ou .webp) para evitar erros
        if img.mode == 'RGBA' or 'A' in img.info.get('transparency', ''):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1]) # Usa o canal alfa como máscara
            img = background
        else:
            img = img.convert('RGB')

        # Aplica a conversão solicitada
        if action == 'bw':
            processed_img = img.convert('L')
            processed_file_name = f"bw_{base_name}.jpg"
            output_format = 'JPEG'
        elif action == 'sepia':
            processed_img = apply_sepia(img)
            processed_file_name = f"sepia_{base_name}.jpg"
            output_format = 'JPEG'
        elif action == 'png':
            processed_img = img
            processed_file_name = f"{base_name}.png"
            output_format = 'PNG'
        elif action == 'jpg':
            processed_img = img
            processed_file_name = f"{base_name}.jpg"
            output_format = 'JPEG'
        elif action == 'image-to-pdf':
            processed_img = img
            processed_file_name = f"{base_name}.pdf"
            output_format = 'PDF'
        else:
            raise ValueError(f"Ação de imagem desconhecida: {action}")

        processed_file_path = os.path.join('/tmp', processed_file_name)
        processed_img.save(processed_file_path, format=output_format)
        print(f"INFO: Imagem processada com sucesso para a ação '{action}'.")

        # --- Upload do Resultado ---
        destination_blob = destination_bucket.blob(processed_file_name)
        destination_blob.upload_from_filename(processed_file_path)
        print(f"SUCESSO: Ficheiro '{processed_file_name}' salvo em '{destination_bucket_name}'.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento do ficheiro '{file_name}': {e}")
    finally:
        # Limpeza segura dos ficheiros temporários
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if processed_file_path and os.path.exists(processed_file_path):
            os.remove(processed_file_path)
        print("INFO: Limpeza de ficheiros temporários concluída.")
