import os
from google.cloud import storage
from PIL import Image
import pillow_heif
import ffmpeg
from docx2pdf import convert  # Nova biblioteca

storage_client = storage.Client()
pillow_heif.register_heif_opener()

def apply_sepia(img):
    if img.mode != 'RGB': img = img.convert('RGB')
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    """ Lê a ação dos metadados e processa ficheiros. """
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

        # --- Roteador de Processamento ---
        
        # LÓGICA PARA IMAGENS
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.heif', '.webp')):
            print(f"INFO: Roteado para processamento de imagem.")
            img = Image.open(temp_input_path)
            if action == 'sepia':
                img = apply_sepia(img)
                processed_file_name = f"{base_name}_sepia.jpg"
                processed_file_path = f"/tmp/{processed_file_name}"
                img.save(processed_file_path, "JPEG")
                print(f"INFO: Imagem processada com filtro sepia.")
            else:
                raise ValueError(f"Ação de imagem desconhecida: {action}")

        # LÓGICA PARA VÍDEOS
        elif file_name.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            print(f"INFO: Roteado para processamento de vídeo.")
            if action == 'extract-audio':
                processed_file_name = f"{base_name}.mp3"
                processed_file_path = f"/tmp/{processed_file_name}"
                (
                    ffmpeg
                    .input(temp_input_path)
                    .output(processed_file_path, format='mp3', acodec='libmp3lame')
                    .run(overwrite_output=True)
                )
                print(f"INFO: Áudio extraído do vídeo com sucesso.")
            else:
                raise ValueError(f"Ação de vídeo desconhecida: {action}")

        # --- NOVA LÓGICA PARA DOCUMENTOS ---
        elif file_name.lower().endswith('.docx'):
            if action == 'docx-to-pdf':
                print(f"INFO: Roteado para conversor de DOCX para PDF.")
                processed_file_name = f"{base_name}.pdf"
                processed_file_path = f"/tmp/{processed_file_name}"
                
                # Executa a conversão
                convert(temp_input_path, processed_file_path)
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
        # Limpeza
        if os.path.exists(temp_input_path): os.remove(temp_input_path)
        if 'processed_file_path' in locals() and os.path.exists(processed_file_path): os.remove(processed_file_path)

