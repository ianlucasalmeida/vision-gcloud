import os
from google.cloud import storage
from PIL import Image, ImageOps
import ffmpeg

storage_client = storage.Client()

def apply_sepia(img):
    """Aplica um filtro de sépia em uma imagem."""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    sepia_filter = Image.new('RGB', img.size, (0, 0, 0))
    # Cria a matriz de cores para o tom sépia
    sepia_matrix = [
        0.393, 0.769, 0.189, 0,
        0.349, 0.686, 0.168, 0,
        0.272, 0.534, 0.131, 0
    ]
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    """
    Função serverless multifuncional acionada por um evento de upload.
    Processa o arquivo baseado na sua extensão e no nome do arquivo.
    """
    bucket_name = event['bucket']
    file_name = event['name']
    print(f"INFO: Novo arquivo '{file_name}' no bucket '{bucket_name}'.")

    # --- Lógica de Roteamento por Nome de Arquivo ---
    # Para controlar a operação, podemos usar prefixos no nome do arquivo
    # Ex: "sepia_minhafoto.jpg" ou "pdf_minhaimagem.png"
    
    action = "default"
    if "_" in os.path.basename(file_name):
        prefix = os.path.basename(file_name).split('_')[0].lower()
        if prefix in ["sepia", "pdf", "jpg", "png", "heif", "webm"]:
            action = prefix

    source_bucket = storage_client.bucket(bucket_name)
    destination_bucket_name = os.environ.get('DESTINATION_BUCKET')
    destination_bucket = storage_client.bucket(destination_bucket_name)

    source_blob = source_bucket.blob(file_name)
    temp_file_path = f"/tmp/{os.path.basename(file_name)}"
    source_blob.download_to_filename(temp_file_path)
    
    processed_file_path = None
    processed_file_name = None

    try:
        original_base_name = "_".join(os.path.basename(file_name).split('_')[1:]) if action != "default" else os.path.basename(file_name)
        base_name = os.path.splitext(original_base_name)[0]

        # --- Roteador de Processamento ---
        
        # LÓGICA PARA IMAGENS
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(temp_file_path)

            if action == "sepia":
                print("INFO: Aplicando filtro Sépia.")
                processed_file_name = f"sepia_{original_base_name}"
                processed_file_path = f"/tmp/{processed_file_name}"
                sepia_img = apply_sepia(img)
                sepia_img.save(processed_file_path)

            elif action == "pdf":
                print("INFO: Convertendo imagem para PDF.")
                processed_file_name = f"pdf_{base_name}.pdf"
                processed_file_path = f"/tmp/{processed_file_name}"
                img.save(processed_file_path, "PDF", resolution=100.0)

            elif action == "jpg":
                print("INFO: Convertendo imagem para JPG.")
                processed_file_name = f"converted_{base_name}.jpg"
                processed_file_path = f"/tmp/{processed_file_name}"
                img.convert('RGB').save(processed_file_path, 'JPEG')

            else: # Ação Padrão: Preto e Branco
                print("INFO: Ação padrão, convertendo para preto e branco.")
                processed_file_name = f"bw_{original_base_name}"
                processed_file_path = f"/tmp/{processed_file_name}"
                img.convert('L').save(processed_file_path)

        # LÓGICA PARA VÍDEO
        elif file_name.lower().endswith(('.mp4', '.mov', '.avi')):
            if action == "webm":
                 print(f"INFO: Convertendo vídeo para WEBM.")
                 processed_file_name = f"converted_{base_name}.webm"
                 processed_file_path = f"/tmp/{processed_file_name}"
                 ffmpeg.input(temp_file_path).output(processed_file_path).run(capture_stdout=True, capture_stderr=True)
            else: # Ação Padrão: Extrair Thumbnail
                print("INFO: Ação padrão, extraindo thumbnail.")
                processed_file_name = f"thumbnail_{base_name}.jpg"
                processed_file_path = f"/tmp/{processed_file_name}"
                ffmpeg.input(temp_file_path, ss=1).output(processed_file_path, vframes=1).run(capture_stdout=True, capture_stderr=True)

        else:
            print(f"AVISO: Tipo de arquivo não suportado.")
            os.remove(temp_file_path)
            return

        # --- Upload do Resultado ---
        if processed_file_path and processed_file_name:
            destination_blob = destination_bucket.blob(processed_file_name)
            destination_blob.upload_from_filename(processed_file_path)
            destination_blob.make_public()
            print(f"SUCESSO: Arquivo '{processed_file_name}' salvo.")
            
    except Exception as e:
        print(f"ERRO CRÍTICO no processamento: {e}")
    finally:
        # Limpeza
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        if processed_file_path and os.path.exists(processed_file_path): os.remove(processed_file_path)