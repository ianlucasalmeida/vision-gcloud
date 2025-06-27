import os
import subprocess
from google.cloud import storage
from PIL import Image
import pillow_heif

# --- Configuração Inicial ---
# Registra o suporte para o formato HEIF/HEIC (requer a biblioteca libheif no sistema)
pillow_heif.register_heif_opener()

def apply_sepia(img):
    """Aplica um filtro de sépia, garantindo que a imagem está em modo RGB."""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    return img.convert('RGB', sepia_matrix)

# --- Função Principal ---
def vision_gcloud_processor(event, context):
    """
    Lê a ação dos metadados e processa ficheiros de imagem e documentos.
    """
    file_data = event
    bucket_name = file_data['bucket']
    file_name = file_data['name'] # Este já é o nome seguro gerado no upload
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    
    # Validação inicial dos metadados
    if not blob or not blob.metadata or 'action' not in blob.metadata:
        print(f"AVISO: Ficheiro '{file_name}' recebido sem o metadado 'action'. A ignorar.")
        return

    action = blob.metadata['action']
    print(f"INFO: Ficheiro '{file_name}' recebido com ação '{action}'.")

    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = client.bucket(destination_bucket_name)

    # Usa os.path.join para segurança e consistência
    temp_input_path = os.path.join('/tmp', os.path.basename(file_name))
    blob.download_to_filename(temp_input_path)
    
    processed_file_path = None
    
    try:
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        
        # --- ROTEADOR DE PROCESSAMENTO ---
        
        # 1. LÓGICA PARA IMAGENS
        if action in ['bw', 'sepia', 'png', 'jpg', 'image-to-pdf']:
            print(f"INFO: Roteado para processador de imagens.")
            img = Image.open(temp_input_path)
            
            # Trata a transparência para evitar erros em conversões
            if img.mode == 'RGBA' or 'A' in img.info.get('transparency', ''):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img_rgb = background
            else:
                img_rgb = img.convert('RGB')

            if action == 'bw':
                processed_img, ext, fmt = img_rgb.convert('L'), '.jpg', 'JPEG'
                processed_file_name = f"bw_{base_name}{ext}"
            elif action == 'sepia':
                processed_img, ext, fmt = apply_sepia(img_rgb), '.jpg', 'JPEG'
                processed_file_name = f"sepia_{base_name}{ext}"
            elif action == 'png':
                processed_img, ext, fmt = img, '.png', 'PNG' # Usa a imagem original para manter a transparência se possível
                processed_file_name = f"{base_name}{ext}"
            elif action == 'jpg':
                processed_img, ext, fmt = img_rgb, '.jpg', 'JPEG'
                processed_file_name = f"{base_name}{ext}"
            elif action == 'image-to-pdf':
                processed_img, ext, fmt = img_rgb, '.pdf', 'PDF'
                processed_file_name = f"{base_name}{ext}"
            
            processed_file_path = os.path.join('/tmp', processed_file_name)
            processed_img.save(processed_file_path, format=fmt, save_all=(action == 'image-to-pdf'))
            print(f"INFO: Imagem processada com sucesso.")

        # 2. LÓGICA PARA DOCUMENTOS
        elif action == 'doc-to-pdf' and file_name.lower().endswith('.docx'):
            # NOTA: Requer que o LibreOffice esteja no container de execução (via Dockerfile).
            print(f"INFO: Roteado para conversor de DOCX.")
            processed_file_name = f"{base_name}.pdf"
            output_dir = '/tmp'
            subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, temp_input_path], check=True)
            processed_file_path = os.path.join(output_dir, processed_file_name)
            print(f"INFO: Documento convertido para PDF.")

        else:
            raise ValueError(f"Ação '{action}' não suportada para o tipo de ficheiro '{file_name}'.")

        # --- Upload do Resultado ---
        destination_blob = destination_bucket.blob(processed_file_name)
        destination_blob.upload_from_filename(processed_file_path)
        print(f"SUCESSO: Ficheiro '{processed_file_name}' salvo em '{destination_bucket_name}'.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento do ficheiro '{file_name}' com ação '{action}': {e}")
    finally:
        # Limpeza segura dos ficheiros temporários
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if processed_file_path and os.path.exists(processed_file_path):
            os.remove(processed_file_path)
        print("INFO: Limpeza de ficheiros temporários concluída.")
