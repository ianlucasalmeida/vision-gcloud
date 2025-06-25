import os
from google.cloud import storage
from PIL import Image

storage_client = storage.Client()

def apply_sepia(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    sepia_matrix = [0.393, 0.769, 0.189, 0, 0.349, 0.686, 0.168, 0, 0.272, 0.534, 0.131, 0]
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    file_data = event
    bucket_name = file_data['bucket']
    file_name = file_data['name']
    
    # --- MUDANÇA IMPORTANTE: Lê a ação dos metadados ---
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    
    if not blob or not blob.metadata or 'action' not in blob.metadata:
        print(f"AVISO: Arquivo '{file_name}' sem metadado 'action'. Ignorando.")
        return

    action = blob.metadata['action']
    print(f"INFO: Arquivo '{file_name}' recebido com ação '{action}'.")

    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = client.bucket(destination_bucket_name)

    temp_file_path = f"/tmp/{os.path.basename(file_name)}"
    blob.download_to_filename(temp_file_path)
    
    processed_file_path = None
    processed_file_name = None

    try:
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        img = Image.open(temp_file_path)
        output_format = 'JPEG' # Padrão
        
        if action == 'bw':
            processed_img = img.convert('L')
            processed_file_name = f"bw_{base_name}.jpg"
        elif action == 'sepia':
            processed_img = apply_sepia(img)
            processed_file_name = f"sepia_{base_name}.jpg"
        elif action == 'pdf':
            output_format = "PDF"
            processed_img = img
            processed_file_name = f"{base_name}.pdf"
        elif action == 'jpg':
            processed_img = img.convert('RGB')
            processed_file_name = f"{base_name}.jpg"
        else:
            print(f"AVISO: Ação '{action}' não suportada.")
            os.remove(temp_file_path)
            return

        processed_file_path = f"/tmp/{processed_file_name}"
        processed_img.save(processed_file_path, output_format)
        print(f"INFO: Arquivo processado e salvo temporariamente em '{processed_file_path}'.")

        # --- Upload do Resultado ---
        destination_blob = destination_bucket.blob(processed_file_name)
        destination_blob.upload_from_filename(processed_file_path)
        print(f"SUCESSO: Arquivo '{processed_file_name}' salvo em '{destination_bucket_name}'.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento: {e}")
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        if processed_file_path and os.path.exists(processed_file_path): os.remove(processed_file_path)
