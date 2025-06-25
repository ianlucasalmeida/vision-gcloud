import os
from google.cloud import storage
from PIL import Image
import pillow_heif
import ffmpeg
from docx2pdf import convert as convert_docx

# Registra o suporte para o formato HEIF/HEIC
pillow_heif.register_heif_opener()

def apply_sepia(img):
    """Aplica um filtro de sépia, garantindo que a imagem está em modo RGB."""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    """ Lê a ação dos metadados e processa ficheiros de imagem, vídeo e documentos. """
    file_data = event
    bucket_name = file_data['bucket']
    file_name = file_data['name']
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    
    if not blob or not blob.metadata or 'action' not in blob.metadata:
        print(f"AVISO: Ficheiro '{file_name}' sem metadado 'action'. Ignorando.")
        return

    action = blob.metadata['action']
    print(f"INFO: Ficheiro '{file_name}' recebido com ação '{action}'.")

    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = client.bucket(destination_bucket_name)

    temp_input_path = f"/tmp/{os.path.basename(file_name)}"
    blob.download_to_filename(temp_input_path)
    
    processed_file_path = None
    processed_file_name = None

    try:
        base_name = os.path.splitext(os.path.basename(file_name))[0]

        # --- ROTEADOR DE PROCESSAMENTO CORRIGIDO ---
        
        # 1. LÓGICA PARA IMAGENS
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.heif', '.webp', '.gif', '.bmp')):
            print(f"INFO: Roteado para processador de imagens.")
            img = Image.open(temp_input_path)
            
            # Garante que imagens com transparência (PNG, WEBP) sejam tratadas corretamente
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3]) # Usa o canal alfa como máscara
                img_rgb = background
            else:
                img_rgb = img.convert('RGB')

            if action == 'bw':
                processed_img = img.convert('L')
                processed_file_name = f"bw_{base_name}.jpg"
                output_format = 'JPEG'
            elif action == 'sepia':
                processed_img = apply_sepia(img)
                processed_file_name = f"sepia_{base_name}.jpg"
                output_format = 'JPEG'
            elif action == 'png':
                processed_img = img # Mantém o original com possível transparência
                processed_file_name = f"{base_name}.png"
                output_format = 'PNG'
            elif action == 'jpg':
                processed_img = img_rgb # Usa a versão com fundo branco se necessário
                processed_file_name = f"{base_name}.jpg"
                output_format = 'JPEG'
            else:
                raise ValueError(f"Ação de imagem desconhecida: {action}")

            processed_file_path = f"/tmp/{processed_file_name}"
            processed_img.save(processed_file_path, format=output_format)
            print(f"INFO: Imagem processada com sucesso para a ação '{action}'.")

        # 2. LÓGICA PARA VÍDEOS
        elif file_name.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            thumb_second = blob.metadata.get('thumb_second', '1')

            if action == 'thumbnail':
                processed_file_name = f"thumbnail_{base_name}.jpg"
                processed_file_path = f"/tmp/{processed_file_name}"
                (
                    ffmpeg
                    .input(temp_input_path, ss=thumb_second)
                    .output(processed_file_path, vframes=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                print(f"INFO: Vídeo processado com sucesso para a ação {action}.")
            else:
                raise ValueError(f"Ação de vídeo desconhecida: {action}")

        # 3. LÓGICA PARA DOCUMENTOS
        elif file_name.lower().endswith('.docx'):
            if action == 'doc-to-pdf':
                print(f"INFO: Roteado para conversor de DOCX para PDF.")
                processed_file_name = f"{base_name}.pdf"
                processed_file_path = f"/tmp/{processed_file_name}"
                
                convert_docx(temp_input_path, processed_file_path)
                
                print(f"INFO: Documento convertido para PDF com sucesso.")
            else:
                raise ValueError(f"Ação de documento desconhecida: {action}")
        else:
            raise ValueError(f"Tipo de ficheiro não suportado: {file_name}")

        # --- Upload do Resultado ---
        destination_blob = destination_bucket.blob(processed_file_name)
        destination_blob.upload_from_filename(processed_file_path)
        print(f"SUCESSO: Ficheiro '{processed_file_name}' salvo em '{destination_bucket_name}'.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento: {e}")
    finally:
        # Limpeza segura dos ficheiros temporários
        if os.path.exists(temp_input_path): os.remove(temp_input_path)
        if processed_file_path and os.path.exists(processed_file_path): os.remove(processed_file_path)
        print("INFO: Limpeza de ficheiros temporários concluída.")
