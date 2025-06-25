import os
from google.cloud import storage
from PIL import Image
import pillow_heif
import ffmpeg
from docx2pdf import convert as convert_docx
# A importação de odt2pdf foi removida.

storage_client = storage.Client()
pillow_heif.register_heif_opener()

def apply_sepia(img):
    if img.mode != 'RGB': img = img.convert('RGB')
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    """ Lê a ação dos metadados e processa ficheiros. """
    # ... (início da função como antes) ...
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
        
        # LÓGICA PARA IMAGENS (sem alterações)
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.heif', '.webp', '.gif', '.bmp')):
            # ... (código para imagens permanece igual)
            pass # Adicione a lógica de imagem aqui

        # LÓGICA PARA VÍDEOS (sem alterações)
        elif file_name.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            # ... (código para vídeos permanece igual) ...
            pass # Adicione a lógica de vídeo aqui

        # --- LÓGICA ATUALIZADA PARA DOCUMENTOS (APENAS .DOCX) ---
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
        # Limpeza
        if os.path.exists(temp_input_path): os.remove(temp_input_path)
        if 'processed_file_path' in locals() and os.path.exists(processed_file_path): os.remove(processed_file_path)

